"""Schemas for employer operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import BaseSchema, TimezoneAwareDatetimeMixin


class AddEmployerInput(BaseSchema):
    """Input schema for adding a new employer."""

    name: str = Field(
        description="Name of the employer organization",
        min_length=1,
        max_length=255,
        examples=["Tech Corp", "Consulting Services LLC"],
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes about the employer",
        max_length=2000,
        examples=["Parent company of multiple subsidiaries", "Remote-first company"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["technology", "remote"], ["consulting", "enterprise"]],
    )


class AddEmployerOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added employer."""

    id: int = Field(
        description="Unique identifier for the employer",
        examples=[1, 42],
    )

    name: str = Field(
        description="Name of the employer",
        examples=["Tech Corp"],
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["technology", "remote"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when employer was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when employer was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )
