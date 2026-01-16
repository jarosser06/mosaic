"""Schemas for project operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    ProjectStatus,
    TimezoneAwareDatetimeMixin,
)


class AddProjectInput(BaseSchema):
    """Input schema for adding a new project."""

    name: str = Field(
        description="Name of the project",
        min_length=1,
        max_length=255,
        examples=["Website Redesign", "Mobile App Development"],
    )

    client_id: int = Field(
        description="ID of the client this project belongs to",
        gt=0,
        examples=[1, 42],
    )

    status: ProjectStatus = Field(
        default=ProjectStatus.ACTIVE,
        description="Current status of the project",
        examples=["active", "paused", "completed"],
    )

    on_behalf_of: int | None = Field(
        default=None,
        description="ID of employer/client on whose behalf work is performed",
        gt=0,
        examples=[1, 5],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description of the project",
        max_length=2000,
        examples=[
            "Complete redesign of company website with modern framework",
            "Native iOS and Android app development",
        ],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["web", "frontend"], ["mobile", "ios", "android"]],
    )


class AddProjectOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added project."""

    id: int = Field(
        description="Unique identifier for the project",
        examples=[1, 42],
    )

    name: str = Field(
        description="Name of the project",
        examples=["Website Redesign"],
    )

    client_id: int = Field(
        description="ID of associated client",
        examples=[1, 42],
    )

    status: ProjectStatus = Field(
        description="Current status",
        examples=["active", "paused", "completed"],
    )

    on_behalf_of: int | None = Field(
        default=None,
        description="ID of employer/client for work attribution",
    )

    description: str | None = Field(
        default=None,
        description="Project description",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["web", "frontend"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when project was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when project was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdateProjectInput(BaseSchema):
    """Input schema for updating an existing project."""

    name: str | None = Field(
        default=None,
        description="New name",
        min_length=1,
        max_length=255,
        examples=["Website Redesign v2"],
    )

    client_id: int | None = Field(
        default=None,
        description="New client ID",
        gt=0,
        examples=[1, 42],
    )

    status: ProjectStatus | None = Field(
        default=None,
        description="New status",
        examples=["active", "paused", "completed"],
    )

    on_behalf_of: int | None = Field(
        default=None,
        description="New employer/client ID for work attribution",
        gt=0,
        examples=[1, 5],
    )

    description: str | None = Field(
        default=None,
        description="New description",
        max_length=2000,
        examples=["Updated project scope"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["web", "frontend", "react"]],
    )


class UpdateProjectOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated project."""

    id: int = Field(
        description="Unique identifier for the project",
        examples=[1, 42],
    )

    name: str = Field(
        description="Name of the project",
        examples=["Website Redesign"],
    )

    client_id: int = Field(
        description="ID of associated client",
        examples=[1, 42],
    )

    status: ProjectStatus = Field(
        description="Current status",
        examples=["active", "paused", "completed"],
    )

    on_behalf_of: int | None = Field(
        default=None,
        description="ID of employer/client for work attribution",
    )

    description: str | None = Field(
        default=None,
        description="Project description",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["web", "frontend"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when project was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when project was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )
