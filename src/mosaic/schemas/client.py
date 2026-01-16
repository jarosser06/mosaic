"""Schemas for client operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    ClientStatus,
    ClientType,
    TimezoneAwareDatetimeMixin,
)


class AddClientInput(BaseSchema):
    """Input schema for adding a new client."""

    name: str = Field(
        description="Name of the client",
        min_length=1,
        max_length=255,
        examples=["Acme Corporation", "Smith & Associates"],
    )

    client_type: ClientType = Field(
        description="Type of client entity",
        examples=["company", "individual"],
    )

    status: ClientStatus = Field(
        default=ClientStatus.ACTIVE,
        description="Current status of the client",
        examples=["active", "past"],
    )

    contact_person_id: int | None = Field(
        default=None,
        description="ID of primary contact person",
        gt=0,
        examples=[1, 42],
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes about the client",
        max_length=2000,
        examples=["Key account, quarterly reviews", "Prefers written proposals"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["enterprise", "long-term"], ["startup", "tech"]],
    )


class AddClientOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added client."""

    id: int = Field(
        description="Unique identifier for the client",
        examples=[1, 42],
    )

    name: str = Field(
        description="Name of the client",
        examples=["Acme Corporation"],
    )

    client_type: ClientType = Field(
        description="Type of client entity",
        examples=["company", "individual"],
    )

    status: ClientStatus = Field(
        description="Current status",
        examples=["active", "past"],
    )

    contact_person_id: int | None = Field(
        default=None,
        description="ID of primary contact person",
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["enterprise", "long-term"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when client was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when client was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdateClientInput(BaseSchema):
    """Input schema for updating an existing client."""

    name: str | None = Field(
        default=None,
        description="New name",
        min_length=1,
        max_length=255,
        examples=["Acme Corp (Updated)"],
    )

    client_type: ClientType | None = Field(
        default=None,
        description="New client type",
        examples=["company", "individual"],
    )

    status: ClientStatus | None = Field(
        default=None,
        description="New status",
        examples=["active", "past"],
    )

    contact_person_id: int | None = Field(
        default=None,
        description="New primary contact person ID",
        gt=0,
        examples=[1, 42],
    )

    notes: str | None = Field(
        default=None,
        description="New notes",
        max_length=2000,
        examples=["Updated account information"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["enterprise", "long-term", "strategic"]],
    )


class UpdateClientOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated client."""

    id: int = Field(
        description="Unique identifier for the client",
        examples=[1, 42],
    )

    name: str = Field(
        description="Name of the client",
        examples=["Acme Corporation"],
    )

    client_type: ClientType = Field(
        description="Type of client entity",
        examples=["company", "individual"],
    )

    status: ClientStatus = Field(
        description="Current status",
        examples=["active", "past"],
    )

    contact_person_id: int | None = Field(
        default=None,
        description="ID of primary contact person",
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["enterprise", "long-term"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when client was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when client was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )
