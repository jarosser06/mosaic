"""Schemas for work session operations."""

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    PrivacyLevel,
    TimeRangeMixin,
    TimezoneAwareDatetimeMixin,
)


class LogWorkSessionInput(BaseSchema, TimezoneAwareDatetimeMixin, TimeRangeMixin):
    """Input schema for logging a new work session."""

    start_time: datetime = Field(
        description="Start time of work session (timezone-aware)",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of work session (timezone-aware)",
        examples=["2026-01-15T17:30:00-05:00"],
    )

    project_id: int = Field(
        description="ID of project this work session belongs to",
        gt=0,
        examples=[1, 42],
    )

    description: str | None = Field(
        default=None,
        description="Optional description of work performed",
        max_length=2000,
        examples=["Implemented user authentication", "Fixed database migration"],
    )

    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE,
        description="Privacy level for this work session",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags for categorization",
        examples=[["backend", "api"], ["frontend", "ui"]],
    )


class LogWorkSessionOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for logged work session."""

    id: int = Field(
        description="Unique identifier for the work session",
        examples=[1, 42],
    )

    start_time: datetime = Field(
        description="Start time of work session",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of work session",
        examples=["2026-01-15T17:30:00-05:00"],
    )

    project_id: int = Field(
        description="ID of associated project",
        examples=[1, 42],
    )

    duration_hours: Decimal = Field(
        description="Calculated duration in hours with half-hour rounding",
        examples=[8.5, 4.0, 2.5],
    )

    description: str | None = Field(
        default=None,
        description="Description of work performed",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this work session",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["backend", "api"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when work session was created",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when work session was last updated",
        examples=["2026-01-15T09:05:00-05:00"],
    )


class UpdateWorkSessionInput(BaseSchema, TimezoneAwareDatetimeMixin, TimeRangeMixin):
    """Input schema for updating an existing work session."""

    start_time: datetime | None = Field(
        default=None,
        description="New start time (timezone-aware)",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    end_time: datetime | None = Field(
        default=None,
        description="New end time (timezone-aware)",
        examples=["2026-01-15T17:30:00-05:00"],
    )

    project_id: int | None = Field(
        default=None,
        description="New project ID",
        gt=0,
        examples=[1, 42],
    )

    description: str | None = Field(
        default=None,
        description="New description",
        max_length=2000,
        examples=["Updated implementation details"],
    )

    privacy_level: PrivacyLevel | None = Field(
        default=None,
        description="New privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["backend", "api", "updated"]],
    )


class UpdateWorkSessionOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated work session."""

    id: int = Field(
        description="Unique identifier for the work session",
        examples=[1, 42],
    )

    start_time: datetime = Field(
        description="Start time of work session",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of work session",
        examples=["2026-01-15T17:30:00-05:00"],
    )

    project_id: int = Field(
        description="ID of associated project",
        examples=[1, 42],
    )

    duration_hours: Decimal = Field(
        description="Calculated duration in hours with half-hour rounding",
        examples=[8.5, 4.0, 2.5],
    )

    description: str | None = Field(
        default=None,
        description="Description of work performed",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this work session",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["backend", "api"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when work session was created",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when work session was last updated",
        examples=["2026-01-15T09:05:00-05:00"],
    )
