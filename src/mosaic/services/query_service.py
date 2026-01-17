"""Query service for flexible multi-entity queries with filtering."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.base import EntityType, PrivacyLevel

if TYPE_CHECKING:
    from ..schemas.query_structured import AggregationSpec, FilterSpec
from ..models.client import Client
from ..models.employer import Employer
from ..models.meeting import Meeting
from ..models.note import Note
from ..models.person import Person
from ..models.project import Project
from ..models.reminder import Reminder
from ..models.work_session import WorkSession


class QueryService:
    """Business logic for flexible cross-entity queries."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize query service.

        Args:
            session: Async database session
        """
        self.session = session

    async def flexible_query(
        self,
        entity_types: Optional[list[EntityType]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        privacy_levels: Optional[list[PrivacyLevel]] = None,
        include_private: bool = True,
        search_text: Optional[str] = None,
        project_id: Optional[int] = None,
        person_id: Optional[int] = None,
        client_id: Optional[int] = None,
        employer_id: Optional[int] = None,
        include_completed: bool = False,
        project_status: Optional[str] = None,
        client_status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, list[Any]]:
        """
        Flexible query across multiple entity types with filters.

        Single-user system so privacy filtering is optional
        (defaults to showing all).

        Args:
            entity_types: List of entity types to query (None = all)
            start_date: Filter by date >= start_date (for dated entities)
            end_date: Filter by date <= end_date (for dated entities)
            privacy_levels: Specific privacy levels to include
            include_private: Include PRIVATE privacy level (default: True)
            search_text: Full-text search on summary/text fields
                (case-insensitive)
            project_id: Filter to specific project
            person_id: Filter to specific person
            client_id: Filter to specific client
            employer_id: Filter to specific employer
            include_completed: Include completed reminders (default: False)
            project_status: Filter projects by status (active, paused, completed)
            client_status: Filter clients by status (active, past)
            limit: Maximum results per entity type

        Returns:
            dict[str, list]: Results grouped by entity type
                Keys: "work_sessions", "meetings", "notes", "reminders",
                      "projects", "people", "clients", "employers", "users"

        Raises:
            ValueError: If end_date is before start_date
        """
        if start_date and end_date and end_date < start_date:
            raise ValueError("end_date must be after or equal to start_date")

        # Default to all entity types if not specified
        if entity_types is None:
            entity_types = [
                EntityType.WORK_SESSION,
                EntityType.MEETING,
                EntityType.NOTE,
                EntityType.PROJECT,
                EntityType.PERSON,
                EntityType.CLIENT,
                EntityType.EMPLOYER,
                EntityType.REMINDER,
            ]

        results: dict[str, list[Any]] = {
            "work_sessions": [],
            "meetings": [],
            "notes": [],
            "reminders": [],
            "projects": [],
            "people": [],
            "clients": [],
            "employers": [],
            "users": [],
        }

        # Query work sessions
        if EntityType.WORK_SESSION in entity_types:
            results["work_sessions"] = await self._query_work_sessions(
                start_date=start_date,
                end_date=end_date,
                privacy_levels=privacy_levels,
                include_private=include_private,
                search_text=search_text,
                project_id=project_id,
                employer_id=employer_id,
                limit=limit,
            )

        # Query meetings
        if EntityType.MEETING in entity_types:
            results["meetings"] = await self._query_meetings(
                start_date=start_date,
                end_date=end_date,
                privacy_levels=privacy_levels,
                include_private=include_private,
                search_text=search_text,
                project_id=project_id,
                person_id=person_id,
                limit=limit,
            )

        # Query notes
        if EntityType.NOTE in entity_types:
            results["notes"] = await self._query_notes(
                privacy_levels=privacy_levels,
                include_private=include_private,
                search_text=search_text,
                limit=limit,
            )

        # Query projects
        if EntityType.PROJECT in entity_types:
            results["projects"] = await self._query_projects(
                search_text=search_text,
                client_id=client_id,
                employer_id=employer_id,
                project_status=project_status,
                limit=limit,
            )

        # Query people
        if EntityType.PERSON in entity_types:
            results["people"] = await self._query_people(
                search_text=search_text,
                limit=limit,
            )

        # Query clients
        if EntityType.CLIENT in entity_types:
            results["clients"] = await self._query_clients(
                search_text=search_text,
                client_status=client_status,
                limit=limit,
            )

        # Query employers
        if EntityType.EMPLOYER in entity_types:
            results["employers"] = await self._query_employers(
                search_text=search_text,
                limit=limit,
            )

        # Query reminders
        if EntityType.REMINDER in entity_types:
            results["reminders"] = await self._query_reminders(
                start_date=start_date,
                end_date=end_date,
                search_text=search_text,
                include_completed=include_completed,
                limit=limit,
            )

        return results

    async def _query_work_sessions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        privacy_levels: Optional[list[PrivacyLevel]] = None,
        include_private: bool = True,
        search_text: Optional[str] = None,
        project_id: Optional[int] = None,
        employer_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[WorkSession]:
        """Query work sessions with filters."""
        query = select(WorkSession).order_by(WorkSession.date.desc())

        # Date filters
        if start_date:
            query = query.where(WorkSession.date >= start_date)
        if end_date:
            query = query.where(WorkSession.date <= end_date)

        # Privacy filters
        if privacy_levels is not None:
            query = query.where(WorkSession.privacy_level.in_(privacy_levels))
        elif not include_private:
            query = query.where(WorkSession.privacy_level != PrivacyLevel.PRIVATE)

        # Project filter
        if project_id:
            query = query.where(WorkSession.project_id == project_id)

        # Employer filter (requires join to project)
        if employer_id:
            query = query.join(Project).where(Project.on_behalf_of_id == employer_id)

        # Text search
        if search_text:
            query = query.where(WorkSession.summary.ilike(f"%{search_text}%"))

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_meetings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        privacy_levels: Optional[list[PrivacyLevel]] = None,
        include_private: bool = True,
        search_text: Optional[str] = None,
        project_id: Optional[int] = None,
        person_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[Meeting]:
        """Query meetings with filters."""
        query = (
            select(Meeting)
            .options(selectinload(Meeting.attendees))
            .order_by(Meeting.start_time.desc())
        )

        # Date filters (convert date to datetime)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(Meeting.start_time >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(Meeting.start_time <= end_dt)

        # Privacy filters
        if privacy_levels is not None:
            query = query.where(Meeting.privacy_level.in_(privacy_levels))
        elif not include_private:
            query = query.where(Meeting.privacy_level != PrivacyLevel.PRIVATE)

        # Project filter
        if project_id:
            query = query.where(Meeting.project_id == project_id)

        # Person filter (requires join to attendees)
        if person_id:
            from ..models.meeting import MeetingAttendee

            query = query.join(MeetingAttendee).where(MeetingAttendee.person_id == person_id)

        # Text search (title and summary)
        if search_text:
            query = query.where(
                or_(
                    Meeting.title.ilike(f"%{search_text}%"),
                    Meeting.summary.ilike(f"%{search_text}%"),
                )
            )

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_notes(
        self,
        privacy_levels: Optional[list[PrivacyLevel]] = None,
        include_private: bool = True,
        search_text: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Note]:
        """Query notes with filters."""
        query = select(Note).order_by(Note.created_at.desc())

        # Privacy filters
        if privacy_levels is not None:
            query = query.where(Note.privacy_level.in_(privacy_levels))
        elif not include_private:
            query = query.where(Note.privacy_level != PrivacyLevel.PRIVATE)

        # Text search
        if search_text:
            query = query.where(Note.text.ilike(f"%{search_text}%"))

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_projects(
        self,
        search_text: Optional[str] = None,
        client_id: Optional[int] = None,
        employer_id: Optional[int] = None,
        project_status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Project]:
        """Query projects with filters."""
        query = select(Project).order_by(Project.name)

        # Status filter
        if project_status:
            query = query.where(Project.status == project_status)

        # Client filter
        if client_id:
            query = query.where(Project.client_id == client_id)

        # Employer filter
        if employer_id:
            query = query.where(Project.on_behalf_of_id == employer_id)

        # Text search (name and description)
        if search_text:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search_text}%"),
                    Project.description.ilike(f"%{search_text}%"),
                )
            )

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_people(
        self,
        search_text: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Person]:
        """Query people with filters."""
        query = select(Person).order_by(Person.full_name)

        # Text search (name and email)
        if search_text:
            query = query.where(
                or_(
                    Person.full_name.ilike(f"%{search_text}%"),
                    Person.email.ilike(f"%{search_text}%"),
                )
            )

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_clients(
        self,
        search_text: Optional[str] = None,
        client_status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Client]:
        """Query clients with filters."""
        query = select(Client).order_by(Client.name)

        # Status filter
        if client_status:
            query = query.where(Client.status == client_status)

        # Text search (name and notes)
        if search_text:
            query = query.where(
                or_(
                    Client.name.ilike(f"%{search_text}%"),
                    Client.notes.ilike(f"%{search_text}%"),
                )
            )

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_employers(
        self,
        search_text: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[Employer]:
        """Query employers with filters."""
        query = select(Employer).order_by(Employer.name)

        # Text search (name and notes)
        if search_text:
            query = query.where(
                or_(
                    Employer.name.ilike(f"%{search_text}%"),
                    Employer.notes.ilike(f"%{search_text}%"),
                )
            )

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _query_reminders(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search_text: Optional[str] = None,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> list[Reminder]:
        """Query reminders with filters."""
        query = select(Reminder).order_by(Reminder.reminder_time)

        # Date filters (convert date to datetime)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(Reminder.reminder_time >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.where(Reminder.reminder_time <= end_dt)

        # Completed filter
        if not include_completed:
            query = query.where(Reminder.is_completed == False)  # noqa: E712

        # Text search
        if search_text:
            query = query.where(Reminder.message.ilike(f"%{search_text}%"))

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def query_notes_by_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        include_private: bool = True,
        limit: Optional[int] = None,
    ) -> list[Note]:
        """
        Query notes attached to a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            include_private: Include private notes (default: True)
            limit: Maximum number of results

        Returns:
            list[Note]: Notes attached to entity
        """
        query = (
            select(Note)
            .where(Note.entity_type == entity_type)
            .where(Note.entity_id == entity_id)
            .order_by(Note.created_at.desc())
        )

        # Privacy filter
        if not include_private:
            query = query.where(Note.privacy_level != PrivacyLevel.PRIVATE)

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def query_reminders_by_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> list[Reminder]:
        """
        Query reminders related to a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            include_completed: Include completed reminders (default: False)
            limit: Maximum number of results

        Returns:
            list[Reminder]: Reminders related to entity
        """
        query = (
            select(Reminder)
            .where(Reminder.related_entity_type == entity_type)
            .where(Reminder.related_entity_id == entity_id)
            .order_by(Reminder.reminder_time)
        )

        # Completed filter
        if not include_completed:
            query = query.where(Reminder.is_completed == False)  # noqa: E712

        # Limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def structured_query(
        self,
        entity_type: EntityType,
        filters: list["FilterSpec"],
        aggregation: "AggregationSpec | None" = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute structured query using query builder.

        Args:
            entity_type: Type of entity to query
            filters: List of filter specifications
            aggregation: Optional aggregation specification
            limit: Maximum results
            offset: Result offset for pagination

        Returns:
            dict: Query results with entities or aggregations
                Format (entities):
                    {
                        "entity_type": "work_session",
                        "results": [<entities>],
                        "total_count": 42
                    }
                Format (aggregation):
                    {
                        "entity_type": "work_session",
                        "aggregation": {
                            "function": "sum",
                            "field": "duration_hours",
                            "result": 42.5
                        },
                        "groups": [...]  # If GROUP BY used
                    }

        Raises:
            ValueError: If query specification is invalid
        """
        # Import here to avoid circular dependency
        from .query_builder import QueryBuilder
        from .result_converter import ResultConverter

        builder = QueryBuilder(self.session)

        # Build query
        query = builder.build_query(
            entity_type=entity_type,
            filters=filters,
            aggregation=aggregation,
            limit=limit,
            offset=offset,
        )

        # Execute query
        result = await self.session.execute(query)

        if aggregation:
            # Handle aggregation results
            func_value = (
                aggregation.function.value
                if hasattr(aggregation.function, "value")
                else str(aggregation.function)
            )
            if aggregation.group_by:
                # Grouped aggregation
                rows = result.all()
                return {
                    "entity_type": (
                        entity_type.value if hasattr(entity_type, "value") else str(entity_type)
                    ),
                    "aggregation": {
                        "function": func_value,
                        "field": aggregation.field,
                        "groups": [
                            {
                                "group_values": list(row[:-1]),
                                "result": row[-1],
                            }
                            for row in rows
                        ],
                    },
                    "total_groups": len(rows),
                }
            else:
                # Global aggregation
                agg_result = result.scalar_one()
                return {
                    "entity_type": (
                        entity_type.value if hasattr(entity_type, "value") else str(entity_type)
                    ),
                    "aggregation": {
                        "function": func_value,
                        "field": aggregation.field,
                        "result": agg_result,
                    },
                }
        else:
            # Handle entity results - convert to Pydantic schemas
            entities = list(result.scalars().all())

            # Convert SQLAlchemy models to Pydantic schemas for JSON serialization
            converter = ResultConverter()
            converted_entities = converter.convert_entity_list(entity_type, entities)

            return {
                "entity_type": (
                    entity_type.value if hasattr(entity_type, "value") else str(entity_type)
                ),
                "results": converted_entities,
                "total_count": len(converted_entities),
            }
