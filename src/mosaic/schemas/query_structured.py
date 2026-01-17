"""Schemas for structured query DSL."""

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from .common import BaseSchema, EntityType


class FilterOperator(str, Enum):
    """Filter operators for structured queries."""

    # Equality operators
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal

    # Comparison operators
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal

    # Set operators
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list

    # String operators
    CONTAINS = "contains"  # Case-insensitive substring match
    STARTS_WITH = "starts_with"  # Case-insensitive starts with
    ENDS_WITH = "ends_with"  # Case-insensitive ends with

    # Null operators
    IS_NULL = "is_null"  # Is NULL
    IS_NOT_NULL = "is_not_null"  # Is NOT NULL

    # Array operators (for tags)
    HAS_TAG = "has_tag"  # Array contains single tag
    HAS_ANY_TAG = "has_any_tag"  # Array overlaps with tag list


class AggregationFunction(str, Enum):
    """Aggregation functions."""

    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"


class FilterSpec(BaseSchema):
    """
    Filter specification for structured queries.

    Supports relationship traversal via dot notation (e.g., "project.client.name").
    """

    field: str = Field(
        description="Field path (supports dot notation for relationships)",
        examples=["name", "project.name", "project.client.name"],
    )

    operator: FilterOperator = Field(
        description="Filter operator",
        examples=["eq", "gt", "contains"],
    )

    value: Any = Field(
        description=(
            "Filter value (supports time shortcuts: today, this_week, etc.). "
            "Ignored for is_null/is_not_null operators."
        ),
        examples=["John Doe", 42, "today", ["tag1", "tag2"]],
    )

    @field_validator("value")
    @classmethod
    def validate_value_for_operator(cls, v: Any, info: Any) -> Any:
        """Validate value is appropriate for operator."""
        if "operator" not in info.data:
            return v

        operator = info.data["operator"]

        # Operators that require list values
        if operator in (FilterOperator.IN, FilterOperator.NOT_IN, FilterOperator.HAS_ANY_TAG):
            if not isinstance(v, list):
                raise ValueError(f"Operator '{operator}' requires a list value")

        # Operators that ignore value
        if operator in (FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL):
            # Value is allowed but will be ignored
            pass

        return v


class AggregationSpec(BaseSchema):
    """
    Aggregation specification.

    Supports grouping by multiple fields with dot notation.
    """

    function: AggregationFunction = Field(
        description="Aggregation function",
        examples=["sum", "count", "avg"],
    )

    field: str = Field(
        description="Field to aggregate (not required for COUNT)",
        examples=["duration_hours", "id"],
    )

    group_by: list[str] = Field(
        default_factory=list,
        description="Fields to group by (supports dot notation)",
        examples=[["project_id"], ["date", "project_id"]],
    )

    @field_validator("field")
    @classmethod
    def validate_field_for_function(cls, v: str, info: Any) -> str:
        """Validate field is provided for functions that require it."""
        if "function" not in info.data:
            return v

        function = info.data["function"]

        # COUNT can work without a field (counts rows)
        if function == AggregationFunction.COUNT and not v:
            return "*"

        # All other functions require a field
        if not v and function != AggregationFunction.COUNT:
            raise ValueError(f"Function '{function}' requires a field to aggregate")

        return v


class StructuredQueryInput(BaseSchema):
    """
    Input for structured query execution.

    Supports filtering, aggregation, and pagination.
    """

    entity_type: EntityType = Field(
        description="Entity type to query",
        examples=["work_session", "meeting"],
    )

    filters: list[FilterSpec] = Field(
        default_factory=list,
        description="Filter specifications (combined with AND logic)",
    )

    aggregation: AggregationSpec | None = Field(
        default=None,
        description="Optional aggregation specification",
    )

    limit: int | None = Field(
        default=None,
        description="Maximum results",
        ge=1,
        le=1000,
    )

    offset: int | None = Field(
        default=None,
        description="Result offset for pagination",
        ge=0,
    )


class AggregationResult(BaseSchema):
    """
    Result of aggregation query.

    Contains either a single result (global aggregation) or grouped results.
    """

    function: str = Field(description="Aggregation function used")
    field: str = Field(description="Field aggregated")

    # Mutually exclusive: either result OR groups
    result: Decimal | int | float | None = Field(
        default=None,
        description="Aggregation result (for global aggregations)",
    )

    groups: list[dict[str, Any]] | None = Field(
        default=None,
        description="Grouped results (for GROUP BY aggregations)",
    )

    @model_validator(mode="after")
    def validate_result_xor_groups(self) -> "AggregationResult":
        """Ensure exactly one of result or groups is set."""
        has_result = self.result is not None
        has_groups = self.groups is not None

        if not has_result and not has_groups:
            raise ValueError("Either 'result' or 'groups' must be provided")

        if has_result and has_groups:
            raise ValueError("Only one of 'result' or 'groups' can be provided")

        return self


class StructuredQueryOutput(BaseSchema):
    """
    Output from structured query execution.

    Contains either entity results or aggregation results.
    """

    entity_type: str = Field(description="Entity type queried")

    # Mutually exclusive: either results OR aggregation
    results: list[Any] | None = Field(
        default=None,
        description="Entity results (if not aggregation)",
    )

    aggregation: AggregationResult | None = Field(
        default=None,
        description="Aggregation results (if aggregation query)",
    )

    total_count: int | None = Field(
        default=None,
        description="Total count of results (for entity queries)",
        ge=0,
    )

    total_groups: int | None = Field(
        default=None,
        description="Total groups (for grouped aggregations)",
        ge=0,
    )

    @model_validator(mode="after")
    def validate_results_xor_aggregation(self) -> "StructuredQueryOutput":
        """Ensure exactly one of results or aggregation is set."""
        has_results = self.results is not None
        has_aggregation = self.aggregation is not None

        if not has_results and not has_aggregation:
            raise ValueError("Either 'results' or 'aggregation' must be provided")

        if has_results and has_aggregation:
            raise ValueError("Only one of 'results' or 'aggregation' can be provided")

        # Ensure total_count is set for entity queries
        if has_results and self.total_count is None:
            raise ValueError("'total_count' is required for entity queries")

        # Ensure total_groups is set for grouped aggregations
        if has_aggregation and has_aggregation and self.aggregation and self.aggregation.groups:
            if self.total_groups is None:
                raise ValueError("'total_groups' is required for grouped aggregations")

        return self
