"""Schemas for work session operations."""

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from mosaic.schemas.common import BaseSchema, PrivacyLevel


class LogWorkSessionInput(BaseSchema):
    """Input schema for logging a new work session."""

    project_id: int = Field(
        description="ID of project this work session belongs to",
        gt=0,
        examples=[1, 42],
    )

    date: date_type = Field(
        description="Work date (YYYY-MM-DD)",
        examples=["2026-01-15"],
    )

    duration_hours: Decimal = Field(
        description="Hours worked (e.g., 2.5)",
        gt=0,
        le=24,
        examples=[2.5, 8.0, 1.5],
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


class LogWorkSessionOutput(BaseSchema):
    """Output schema for logged work session."""

    id: int = Field(
        description="Unique identifier for the work session",
        examples=[1, 42],
    )

    project_id: int = Field(
        description="ID of associated project",
        examples=[1, 42],
    )

    date: date_type = Field(
        description="Work date",
        examples=["2026-01-15"],
    )

    duration_hours: Decimal = Field(
        description="Duration in hours",
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


class UpdateWorkSessionInput(BaseSchema):
    """Input schema for updating an existing work session."""

    project_id: int | None = Field(
        default=None,
        description="New project ID",
        gt=0,
        examples=[1, 42],
    )

    date: date_type | None = Field(
        default=None,
        description="New work date (YYYY-MM-DD)",
        examples=["2026-01-15"],
    )

    duration_hours: Decimal | None = Field(
        default=None,
        description="New hours worked (e.g., 2.5)",
        gt=0,
        le=24,
        examples=[2.5, 8.0, 1.5],
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


class UpdateWorkSessionOutput(BaseSchema):
    """Output schema for updated work session."""

    id: int = Field(
        description="Unique identifier for the work session",
        examples=[1, 42],
    )

    project_id: int = Field(
        description="ID of associated project",
        examples=[1, 42],
    )

    date: date_type = Field(
        description="Work date",
        examples=["2026-01-15"],
    )

    duration_hours: Decimal = Field(
        description="Duration in hours",
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


class DeleteWorkSessionInput(BaseSchema):
    """Input schema for deleting a work session."""

    work_session_id: int = Field(
        description="ID of the work session to delete",
        gt=0,
        examples=[1, 42],
    )


class DeleteWorkSessionOutput(BaseSchema):
    """Output schema for deleted work session confirmation."""

    success: bool = Field(
        description="Whether the deletion was successful",
        examples=[True],
    )

    message: str = Field(
        description="Human-readable confirmation message",
        examples=["Work session deleted successfully"],
    )
