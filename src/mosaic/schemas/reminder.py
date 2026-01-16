"""Schemas for reminder operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    EntityType,
    TimezoneAwareDatetimeMixin,
)


class AddReminderInput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Input schema for adding a new reminder."""

    reminder_time: datetime = Field(
        description="When to trigger the reminder (timezone-aware)",
        examples=["2026-01-20T09:00:00-05:00"],
    )

    message: str = Field(
        description="Reminder message",
        min_length=1,
        max_length=1000,
        examples=["Call client about project status", "Submit timesheet"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of entity this reminder is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of the entity this reminder is attached to",
        gt=0,
        examples=[1, 42],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["urgent", "call"], ["admin", "timesheet"]],
    )


class AddReminderOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added reminder."""

    id: int = Field(
        description="Unique identifier for the reminder",
        examples=[1, 42],
    )

    reminder_time: datetime = Field(
        description="When the reminder will trigger",
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

    updated_at: datetime = Field(
        description="Timestamp when reminder was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class CompleteReminderInput(BaseSchema):
    """Input schema for marking a reminder as complete."""

    reminder_id: int = Field(
        description="ID of the reminder to complete",
        gt=0,
        examples=[1, 42],
    )


class CompleteReminderOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for completed reminder."""

    id: int = Field(
        description="Unique identifier for the reminder",
        examples=[1, 42],
    )

    reminder_time: datetime = Field(
        description="Original reminder time",
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

    completed_at: datetime = Field(
        description="When the reminder was completed",
        examples=["2026-01-20T09:15:00-05:00"],
    )

    snoozed_until: datetime | None = Field(
        default=None,
        description="Snoozed until timestamp (should be null after completion)",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["urgent", "call"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when reminder was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when reminder was last updated",
        examples=["2026-01-20T09:15:00-05:00"],
    )


class SnoozeReminderInput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Input schema for snoozing a reminder."""

    reminder_id: int = Field(
        description="ID of the reminder to snooze",
        gt=0,
        examples=[1, 42],
    )

    snooze_until: datetime = Field(
        description="New time to trigger the reminder (timezone-aware)",
        examples=["2026-01-20T14:00:00-05:00"],
    )


class SnoozeReminderOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for snoozed reminder."""

    id: int = Field(
        description="Unique identifier for the reminder",
        examples=[1, 42],
    )

    reminder_time: datetime = Field(
        description="Original reminder time",
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
        description="Completion timestamp (null if not completed)",
    )

    snoozed_until: datetime = Field(
        description="New reminder time after snooze",
        examples=["2026-01-20T14:00:00-05:00"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["urgent", "call"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when reminder was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when reminder was last updated",
        examples=["2026-01-20T09:00:00-05:00"],
    )
