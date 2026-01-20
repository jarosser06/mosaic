"""Schemas for action item operations."""

from datetime import datetime

from pydantic import Field

from mosaic.models.base import ActionItemStatus
from mosaic.schemas.common import (
    BaseSchema,
    EntityType,
    PrivacyLevel,
    TimezoneAwareDatetimeMixin,
)


class AddActionItemInput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Input schema for adding a new action item."""

    title: str = Field(
        description="Action item title/summary",
        min_length=1,
        max_length=500,
        examples=["Fix login bug", "Review PR #123", "Update documentation"],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description of the action item",
        max_length=5000,
        examples=["Login form validation is not working correctly on mobile devices"],
    )

    status: ActionItemStatus = Field(
        default=ActionItemStatus.PENDING,
        description="Action item status",
        examples=["pending", "in_progress", "completed", "cancelled"],
    )

    due_date: datetime | None = Field(
        default=None,
        description="Due date for the action item (timezone-aware)",
        examples=["2026-01-25T17:00:00-05:00"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of entity this action item is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of the entity this action item is attached to",
        gt=0,
        examples=[1, 42],
    )

    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE,
        description="Privacy level for this action item",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["urgent", "bug"], ["documentation", "tech-debt"]],
    )


class AddActionItemOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added action item."""

    id: int = Field(
        description="Unique identifier for the action item",
        examples=[1, 42],
    )

    title: str = Field(
        description="Action item title",
        examples=["Fix login bug"],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description",
    )

    status: ActionItemStatus = Field(
        description="Current status",
        examples=["pending"],
    )

    due_date: datetime | None = Field(
        default=None,
        description="Due date (null if not set)",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="When the action item was completed (null if not completed)",
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
        description="Privacy level",
        examples=["private"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["urgent", "bug"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when action item was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when action item was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdateActionItemInput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Input schema for updating an action item."""

    action_item_id: int = Field(
        description="ID of the action item to update",
        gt=0,
        examples=[1, 42],
    )

    title: str | None = Field(
        default=None,
        description="Updated title",
        min_length=1,
        max_length=500,
    )

    description: str | None = Field(
        default=None,
        description="Updated description",
        max_length=5000,
    )

    status: ActionItemStatus | None = Field(
        default=None,
        description="Updated status (auto-sets completed_at if changing to completed)",
        examples=["pending", "in_progress", "completed", "cancelled"],
    )

    due_date: datetime | None = Field(
        default=None,
        description="Updated due date",
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Updated entity type",
    )

    entity_id: int | None = Field(
        default=None,
        description="Updated entity ID",
        gt=0,
    )

    privacy_level: PrivacyLevel | None = Field(
        default=None,
        description="Updated privacy level",
    )

    tags: list[str] | None = Field(
        default=None,
        description="Updated tags",
    )


class UpdateActionItemOutput(AddActionItemOutput):
    """Output schema for updated action item."""

    pass


class ListActionItemsInput(BaseSchema):
    """Input schema for listing/filtering action items."""

    status: ActionItemStatus | None = Field(
        default=None,
        description="Filter by action item status",
        examples=["pending", "in_progress", "completed", "cancelled"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Filter by entity type the action item is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="Filter by specific entity ID",
        gt=0,
        examples=[1, 42],
    )

    overdue_only: bool = Field(
        default=False,
        description="Filter to only show overdue action items (active items past due date)",
        examples=[False, True],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Filter by tags (returns action items with ANY of these tags)",
        examples=[["urgent"], ["bug", "tech-debt"]],
    )


class ActionItemItem(BaseSchema, TimezoneAwareDatetimeMixin):
    """Individual action item in list results."""

    id: int = Field(
        description="Unique identifier",
        examples=[1, 42],
    )

    title: str = Field(
        description="Action item title",
        examples=["Fix login bug"],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description",
    )

    status: ActionItemStatus = Field(
        description="Current status",
        examples=["pending"],
    )

    due_date: datetime | None = Field(
        default=None,
        description="Due date",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="When completed",
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Attached entity type",
    )

    entity_id: int | None = Field(
        default=None,
        description="Attached entity ID",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["urgent"], []],
    )

    created_at: datetime = Field(
        description="When created",
    )

    updated_at: datetime = Field(
        description="When last updated",
    )


class ListActionItemsOutput(BaseSchema):
    """Output schema for action item list."""

    action_items: list[ActionItemItem] = Field(
        description="List of action items matching the filters",
        examples=[[]],
    )

    total_count: int = Field(
        description="Total number of action items returned",
        examples=[0, 5, 42],
    )


class DeleteActionItemInput(BaseSchema):
    """Input schema for deleting an action item."""

    action_item_id: int = Field(
        description="ID of the action item to delete",
        gt=0,
        examples=[1, 42],
    )


class DeleteActionItemOutput(BaseSchema):
    """Output schema for deleted action item confirmation."""

    success: bool = Field(
        description="Whether the deletion was successful",
        examples=[True],
    )

    message: str = Field(
        description="Confirmation message",
        examples=["Action item deleted successfully"],
    )
