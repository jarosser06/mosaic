"""Schemas for note operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    EntityType,
    PrivacyLevel,
    TimezoneAwareDatetimeMixin,
)


class AddNoteInput(BaseSchema):
    """Input schema for adding a new note."""

    content: str = Field(
        description="Content of the note",
        min_length=1,
        max_length=10000,
        examples=[
            "Remember to follow up on proposal by Friday",
            "Key points from today's discussion...",
        ],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of entity this note is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of the entity this note is attached to",
        gt=0,
        examples=[1, 42],
    )

    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE,
        description="Privacy level for this note",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["important", "follow-up"], ["idea", "brainstorm"]],
    )


class AddNoteOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added note."""

    id: int = Field(
        description="Unique identifier for the note",
        examples=[1, 42],
    )

    content: str = Field(
        description="Content of the note",
        examples=["Remember to follow up on proposal by Friday"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this note",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["important", "follow-up"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when note was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when note was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdateNoteInput(BaseSchema):
    """Input schema for updating an existing note."""

    content: str | None = Field(
        default=None,
        description="New content",
        min_length=1,
        max_length=10000,
        examples=["Updated note content with more details"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="New entity type",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="New entity ID",
        gt=0,
        examples=[1, 42],
    )

    privacy_level: PrivacyLevel | None = Field(
        default=None,
        description="New privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["important", "follow-up", "urgent"]],
    )


class UpdateNoteOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated note."""

    id: int = Field(
        description="Unique identifier for the note",
        examples=[1, 42],
    )

    content: str = Field(
        description="Content of the note",
        examples=["Remember to follow up on proposal by Friday"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this note",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["important", "follow-up"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when note was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when note was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )
