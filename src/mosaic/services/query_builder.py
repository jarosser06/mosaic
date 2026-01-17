"""QueryBuilder service for converting structured queries to SQLAlchemy."""

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ..models import (
    Client,
    Employer,
    Meeting,
    MeetingAttendee,
    Note,
    Person,
    Project,
    Reminder,
    WorkSession,
)
from ..models.base import EntityType
from ..schemas.query_structured import (
    AggregationFunction,
    AggregationSpec,
    FilterOperator,
    FilterSpec,
)


class QueryBuilder:
    """
    Converts structured query DSL to SQLAlchemy queries.

    Responsibilities:
    - Parse filter specifications into WHERE clauses
    - Handle relationship path traversal (e.g., "project.client.name")
    - Map operators to SQLAlchemy expressions
    - Build aggregation queries with GROUP BY
    - Support time shortcuts (today, this_week, etc.)

    SOLID Principles:
    - Single Responsibility: Only builds SQLAlchemy queries from specs
    - Open-Closed: Extend via operator mapping, not modification
    - Dependency Inversion: Depends on schema abstractions
    """

    # Relationship path mappings
    # Maps "entity.relationship.field" to SQLAlchemy join paths
    RELATIONSHIP_PATHS: dict[EntityType, dict[str, tuple[type[Any], ...]]] = {
        EntityType.WORK_SESSION: {
            "project": (Project,),
            "project.client": (Project, Client),
            "project.client.contact_person": (Project, Client, Person),
            "project.employer": (Project, Employer),
        },
        EntityType.MEETING: {
            "project": (Project,),
            "project.client": (Project, Client),
            "project.employer": (Project, Employer),
            "attendees": (MeetingAttendee,),
            "attendees.person": (MeetingAttendee, Person),
        },
        EntityType.PROJECT: {
            "client": (Client,),
            "client.contact_person": (Client, Person),
            "employer": (Employer,),
        },
        EntityType.CLIENT: {
            "contact_person": (Person,),
        },
        # Base entities with no relationships
        EntityType.PERSON: {},
        EntityType.EMPLOYER: {},
        EntityType.NOTE: {},
        EntityType.REMINDER: {},
    }

    # Field name mappings from schema field names to model field names
    # Maps "entity_type" -> {"schema_field": "model_field"}
    FIELD_NAME_MAPPINGS: dict[EntityType, dict[str, str]] = {
        EntityType.PROJECT: {
            "on_behalf_of": "on_behalf_of_id",
        },
        # Other entity types use matching field names
        EntityType.WORK_SESSION: {},
        EntityType.MEETING: {},
        EntityType.CLIENT: {},
        EntityType.PERSON: {},
        EntityType.EMPLOYER: {},
        EntityType.NOTE: {},
        EntityType.REMINDER: {},
    }

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize QueryBuilder.

        Args:
            session: Async database session
        """
        self.session = session

    def build_query(
        self,
        entity_type: EntityType,
        filters: list[FilterSpec],
        aggregation: AggregationSpec | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[Any]:
        """
        Build SQLAlchemy query from structured specifications.

        Args:
            entity_type: Type of entity to query
            filters: List of filter specifications
            aggregation: Optional aggregation specification
            limit: Maximum results
            offset: Result offset for pagination

        Returns:
            Select: SQLAlchemy select statement

        Raises:
            ValueError: If entity_type is invalid or field path is malformed
        """
        from sqlalchemy.orm import selectinload

        # Get base model class
        model = self._get_model_class(entity_type)

        if aggregation:
            # Build aggregation query
            query = self._build_aggregation_query(model, aggregation, filters)
        else:
            # Build entity query
            query = select(model)

            # Add eager loading for relationships that ResultConverter needs
            # This prevents lazy loading errors in async context
            if entity_type == EntityType.MEETING:
                query = query.options(selectinload(model.attendees))

            # Collect required relationship paths for joins
            join_paths_needed: set[str] = set()

            # Apply filters and collect join paths
            for filter_spec in filters:
                parts = filter_spec.field.split(".")
                if len(parts) > 1:
                    # This field requires joins
                    relationship_path = ".".join(parts[:-1])
                    join_paths_needed.add(relationship_path)

                # Parse field to get column
                column = self._parse_field_path(model, filter_spec.field)

                # Resolve value (handle time shortcuts)
                value = self._resolve_filter_value(filter_spec.value)

                # Apply operator
                condition = self._apply_operator(column, filter_spec.operator, value)
                query = query.where(condition)

            # Apply joins for each relationship path
            for rel_path in sorted(join_paths_needed):
                query = self._apply_joins_for_path(query, model, entity_type, rel_path)

            # Apply ordering (default: created_at DESC)
            if hasattr(model, "created_at"):
                query = query.order_by(model.created_at.desc())
            elif hasattr(model, "start_time"):
                query = query.order_by(model.start_time.desc())

            # Apply pagination
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

        return query

    def _build_aggregation_query(
        self,
        model: type[Any],
        aggregation: AggregationSpec,
        filters: list[FilterSpec],
    ) -> Select[Any]:
        """
        Build aggregation query with GROUP BY.

        Args:
            model: SQLAlchemy model class
            aggregation: Aggregation specification
            filters: Filter specifications

        Returns:
            Select: SQLAlchemy select with aggregation
        """
        # Parse field path for aggregation field
        if aggregation.field != "*":
            agg_column = self._parse_field_path(model, aggregation.field)
        else:
            # For COUNT(*), use model itself
            agg_column = None

        # Apply aggregation function
        agg_expr = self._apply_aggregation_function(
            aggregation.function,
            agg_column if agg_column is not None else model.id,
        )

        # Parse GROUP BY columns and track needed joins
        group_columns = []
        join_paths_needed: set[str] = set()

        if aggregation.group_by:
            for field_path in aggregation.group_by:
                group_columns.append(self._parse_field_path(model, field_path))
                # Track if this field requires a join
                parts = field_path.split(".")
                if len(parts) > 1:
                    relationship_path = ".".join(parts[:-1])
                    join_paths_needed.add(relationship_path)

        # Build query with aggregation
        if aggregation.group_by:
            query = select(*group_columns, agg_expr)
        else:
            # Global aggregation (no GROUP BY)
            query = select(agg_expr)

        # Apply joins needed for GROUP BY columns
        entity_type = self._get_entity_type(model)
        for rel_path in sorted(join_paths_needed):
            query = self._apply_joins_for_path(query, model, entity_type, rel_path)

        # Apply filters and their joins
        for filter_spec in filters:
            # Track filter join needs
            parts = filter_spec.field.split(".")
            if len(parts) > 1:
                relationship_path = ".".join(parts[:-1])
                if relationship_path not in join_paths_needed:
                    # Add join if not already added for GROUP BY
                    query = self._apply_joins_for_path(query, model, entity_type, relationship_path)
                    join_paths_needed.add(relationship_path)

            # Parse and apply filter
            column = self._parse_field_path(model, filter_spec.field)
            value = self._resolve_filter_value(filter_spec.value)
            condition = self._apply_operator(column, filter_spec.operator, value)
            query = query.where(condition)

        # Apply GROUP BY
        if aggregation.group_by:
            query = query.group_by(*group_columns)

        return query

    def _apply_filter(
        self,
        query: Select[Any],
        model: type[Any],
        filter_spec: FilterSpec,
    ) -> Select[Any]:
        """
        Apply filter specification to query.

        Args:
            query: Current query
            model: Base model class
            filter_spec: Filter specification

        Returns:
            Select: Query with filter applied
        """
        # Parse field path (handles relationships)
        column = self._parse_field_path(model, filter_spec.field)

        # Resolve value (handle time shortcuts)
        value = self._resolve_filter_value(filter_spec.value)

        # Apply operator
        condition = self._apply_operator(
            column,
            filter_spec.operator,
            value,
        )

        return query.where(condition)

    def _apply_operator(
        self,
        column: ColumnElement[Any],
        operator: FilterOperator,
        value: Any,
    ) -> Any:
        """
        Map filter operator to SQLAlchemy expression.

        Args:
            column: SQLAlchemy column
            operator: Filter operator enum
            value: Filter value

        Returns:
            Boolean expression

        Raises:
            ValueError: If operator is not supported
        """
        if operator == FilterOperator.EQ:
            return column == value
        elif operator == FilterOperator.NE:
            return column != value
        elif operator == FilterOperator.GT:
            return column > value
        elif operator == FilterOperator.GTE:
            return column >= value
        elif operator == FilterOperator.LT:
            return column < value
        elif operator == FilterOperator.LTE:
            return column <= value
        elif operator == FilterOperator.IN:
            return column.in_(value)
        elif operator == FilterOperator.NOT_IN:
            return column.not_in(value)
        elif operator == FilterOperator.CONTAINS:
            return column.ilike(f"%{value}%")
        elif operator == FilterOperator.STARTS_WITH:
            return column.ilike(f"{value}%")
        elif operator == FilterOperator.ENDS_WITH:
            return column.ilike(f"%{value}")
        elif operator == FilterOperator.IS_NULL:
            return column.is_(None)
        elif operator == FilterOperator.IS_NOT_NULL:
            return column.is_not(None)
        elif operator == FilterOperator.HAS_TAG:
            # PostgreSQL array contains operator (@>)
            # Check if array contains single value
            return column.op("@>")([value])
        elif operator == FilterOperator.HAS_ANY_TAG:
            # PostgreSQL array overlap operator (&&)
            return column.op("&&")(value)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _parse_field_path(
        self,
        base_model: type[Any],
        field_path: str,
    ) -> Any:
        """
        Parse field path with relationships into SQLAlchemy column.

        Translates schema field names to model field names using FIELD_NAME_MAPPINGS.

        Examples:
            "name" -> WorkSession.name
            "project.name" -> Project.name (with join)
            "project.client.name" -> Client.name (with joins)
            "on_behalf_of" -> Project.on_behalf_of_id (field name translation)

        Args:
            base_model: Base SQLAlchemy model
            field_path: Dot-separated field path

        Returns:
            SQLAlchemy column expression

        Raises:
            ValueError: If field path is invalid
        """
        parts = field_path.split(".")

        if len(parts) == 1:
            # Simple field on base model
            entity_type = self._get_entity_type(base_model)
            field_name = parts[0]

            # Translate schema field name to model field name if mapping exists
            if entity_type in self.FIELD_NAME_MAPPINGS:
                field_name = self.FIELD_NAME_MAPPINGS[entity_type].get(field_name, field_name)

            if not hasattr(base_model, field_name):
                raise ValueError(f"Field {field_name} not found on {base_model.__name__}")
            return getattr(base_model, field_name)

        # Relationship traversal required
        # Get join path from RELATIONSHIP_PATHS
        entity_type = self._get_entity_type(base_model)
        relationship_path = ".".join(parts[:-1])
        field_name = parts[-1]

        if entity_type not in self.RELATIONSHIP_PATHS:
            raise ValueError(f"No relationship mappings for {entity_type}")

        if relationship_path not in self.RELATIONSHIP_PATHS[entity_type]:
            raise ValueError(f"Relationship path {relationship_path} not found for {entity_type}")

        # Get target model (last in join path)
        join_models = self.RELATIONSHIP_PATHS[entity_type][relationship_path]
        target_model = join_models[-1]

        # Translate schema field name to model field name for target model
        target_entity_type = self._get_entity_type(target_model)
        if target_entity_type in self.FIELD_NAME_MAPPINGS:
            field_name = self.FIELD_NAME_MAPPINGS[target_entity_type].get(field_name, field_name)

        if not hasattr(target_model, field_name):
            raise ValueError(f"Field {field_name} not found on {target_model.__name__}")

        return getattr(target_model, field_name)

    def _parse_field_path_with_joins(
        self,
        base_model: type[Any],
        field_path: str,
    ) -> tuple[Any, list[type[Any]]]:
        """
        Parse field path and return column with required joins.

        Args:
            base_model: Base SQLAlchemy model
            field_path: Dot-separated field path

        Returns:
            tuple: (column, list of models to join)

        Raises:
            ValueError: If field path is invalid
        """
        parts = field_path.split(".")

        if len(parts) == 1:
            # Simple field on base model - no joins needed
            if not hasattr(base_model, parts[0]):
                raise ValueError(f"Field {parts[0]} not found on {base_model.__name__}")
            return getattr(base_model, parts[0]), []

        # Relationship traversal - get join path
        entity_type = self._get_entity_type(base_model)
        relationship_path = ".".join(parts[:-1])
        field_name = parts[-1]

        if entity_type not in self.RELATIONSHIP_PATHS:
            raise ValueError(f"No relationship mappings for {entity_type}")

        if relationship_path not in self.RELATIONSHIP_PATHS[entity_type]:
            raise ValueError(f"Relationship path {relationship_path} not found for {entity_type}")

        # Get join models
        join_models = self.RELATIONSHIP_PATHS[entity_type][relationship_path]
        target_model = join_models[-1]

        if not hasattr(target_model, field_name):
            raise ValueError(f"Field {field_name} not found on {target_model.__name__}")

        return getattr(target_model, field_name), list(join_models)

    def _apply_joins_for_path(
        self,
        query: Select[Any],
        base_model: type[Any],
        entity_type: EntityType,
        relationship_path: str,
    ) -> Select[Any]:
        """
        Apply joins for a relationship path.

        Args:
            query: Current query
            base_model: Base model class
            entity_type: Entity type being queried
            relationship_path: Dot-separated relationship path (e.g., "project.client")

        Returns:
            Select: Query with joins applied

        Raises:
            ValueError: If relationship path is invalid
        """
        # Split path into parts
        parts = relationship_path.split(".")

        # Start from base model
        current_model = base_model

        # Apply joins step by step
        for part in parts:
            if not hasattr(current_model, part):
                raise ValueError(f"Model {current_model.__name__} has no relationship '{part}'")

            # Get the relationship attribute
            rel_attr = getattr(current_model, part)

            # Apply join using relationship attribute
            query = query.join(rel_attr)

            # Get the target model for next iteration
            # The relationship property has a mapper with the class_
            if hasattr(rel_attr.property, "mapper"):
                current_model = rel_attr.property.mapper.class_
            else:
                raise ValueError(f"Cannot determine target model for relationship '{part}'")

        return query

    def _apply_aggregation_function(
        self,
        function: AggregationFunction,
        column: ColumnElement[Any],
    ) -> Any:
        """
        Apply aggregation function to column.

        Args:
            function: Aggregation function enum
            column: Column to aggregate

        Returns:
            Aggregated expression

        Raises:
            ValueError: If function is not supported
        """
        if function == AggregationFunction.COUNT:
            return func.count(column)
        elif function == AggregationFunction.SUM:
            return func.sum(column)
        elif function == AggregationFunction.AVG:
            return func.avg(column)
        elif function == AggregationFunction.MIN:
            return func.min(column)
        elif function == AggregationFunction.MAX:
            return func.max(column)
        elif function == AggregationFunction.COUNT_DISTINCT:
            return func.count(func.distinct(column))
        else:
            raise ValueError(f"Unsupported aggregation function: {function}")

    def _resolve_filter_value(self, value: Any) -> Any:
        """
        Resolve filter value (handle time shortcuts).

        Time shortcuts:
            - "today" -> date.today()
            - "this_week" -> start of current week
            - "this_month" -> start of current month
            - "this_year" -> start of current year

        Args:
            value: Raw filter value

        Returns:
            Any: Resolved value
        """
        if not isinstance(value, str):
            return value

        # Handle time shortcuts
        if value == "today":
            return date.today()
        elif value == "this_week":
            today = date.today()
            # Start of week (Monday)
            return today - timedelta(days=today.weekday())
        elif value == "this_month":
            return date.today().replace(day=1)
        elif value == "this_year":
            return date.today().replace(month=1, day=1)
        elif value == "now":
            return datetime.now()

        return value

    def _get_model_class(self, entity_type: EntityType) -> type[Any]:
        """
        Get SQLAlchemy model class from entity type.

        Args:
            entity_type: Entity type enum

        Returns:
            type: SQLAlchemy model class

        Raises:
            ValueError: If entity_type is not supported
        """
        mapping = {
            EntityType.WORK_SESSION: WorkSession,
            EntityType.MEETING: Meeting,
            EntityType.PROJECT: Project,
            EntityType.CLIENT: Client,
            EntityType.PERSON: Person,
            EntityType.EMPLOYER: Employer,
            EntityType.NOTE: Note,
            EntityType.REMINDER: Reminder,
        }

        if entity_type not in mapping:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        return mapping[entity_type]

    def _get_entity_type(self, model: type[Any]) -> EntityType:
        """
        Get entity type from SQLAlchemy model class.

        Args:
            model: SQLAlchemy model class

        Returns:
            EntityType: Entity type enum

        Raises:
            ValueError: If model is not recognized
        """
        reverse_mapping = {
            WorkSession: EntityType.WORK_SESSION,
            Meeting: EntityType.MEETING,
            Project: EntityType.PROJECT,
            Client: EntityType.CLIENT,
            Person: EntityType.PERSON,
            Employer: EntityType.EMPLOYER,
            Note: EntityType.NOTE,
            Reminder: EntityType.REMINDER,
        }

        if model not in reverse_mapping:
            raise ValueError(f"Unknown model: {model}")

        return reverse_mapping[model]
