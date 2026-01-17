"""Schemas for reminder management operations (list, delete, bulk complete)."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from mosaic.schemas.common import BaseSchema, EntityType, TimezoneAwareDatetimeMixin


class ReminderStatus(str, Enum):
    """Reminder status filter options."""

    ALL = "all"
    ACTIVE = "active"
    COMPLETED = "completed"
    SNOOZED = "snoozed"


class ListRemindersInput(BaseSchema):
    """Input schema for listing/filtering reminders."""

    status: ReminderStatus = Field(
        default=ReminderStatus.ALL,
        description="Filter by reminder status: all, active, completed, or snoozed",
        examples=["all", "active", "completed", "snoozed"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Filter by entity type the reminder is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="Filter by specific entity ID",
        gt=0,
        examples=[1, 42],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Filter by tags (returns reminders with ANY of these tags)",
        examples=[["urgent"], ["call", "admin"]],
    )


class ReminderItem(BaseSchema, TimezoneAwareDatetimeMixin):
    """Individual reminder in list results."""

    id: int = Field(
        description="Unique identifier for the reminder",
        examples=[1, 42],
    )

    reminder_time: datetime = Field(
        description="When the reminder is/was scheduled to trigger",
        examples=["2026-01-20T09:00:00-05:00"],
    )

    message: str = Field(
        description="Reminder message",
        examples=["Call client about project status"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="When the reminder was completed (null if not completed)",
    )

    snoozed_until: datetime | None = Field(
        default=None,
        description="When the reminder is snoozed until (null if not snoozed)",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["urgent", "call"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when reminder was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class ListRemindersOutput(BaseSchema):
    """Output schema for reminder list."""

    reminders: list[ReminderItem] = Field(
        description="List of reminders matching the filters",
        examples=[[]],
    )

    total_count: int = Field(
        description="Total number of reminders returned",
        examples=[0, 5, 42],
    )


class DeleteReminderInput(BaseSchema):
    """Input schema for deleting a reminder."""

    reminder_id: int = Field(
        description="ID of the reminder to delete",
        gt=0,
        examples=[1, 42],
    )


class DeleteReminderOutput(BaseSchema):
    """Output schema for deleted reminder confirmation."""

    success: bool = Field(
        description="Whether the deletion was successful",
        examples=[True],
    )

    message: str = Field(
        description="Human-readable confirmation message",
        examples=["Reminder 42 deleted successfully"],
    )


class BulkCompleteRemindersInput(BaseSchema):
    """Input schema for bulk completing multiple reminders."""

    reminder_ids: list[int] = Field(
        description="List of reminder IDs to mark as completed",
        min_length=1,
        examples=[[1, 2, 3], [42]],
    )


class BulkCompleteRemindersOutput(BaseSchema):
    """Output schema for bulk complete operation."""

    completed_count: int = Field(
        description="Number of reminders successfully marked as completed",
        examples=[0, 3, 10],
    )

    failed_count: int = Field(
        description="Number of reminders that failed to complete",
        examples=[0, 1],
    )

    failed_ids: list[int] = Field(
        description="List of reminder IDs that failed to complete",
        examples=[[], [5, 7]],
    )

    message: str = Field(
        description="Human-readable summary of the operation",
        examples=[
            "Successfully completed 3 reminders",
            "Completed 2 reminders, failed 1 (IDs: [5])",
        ],
    )
