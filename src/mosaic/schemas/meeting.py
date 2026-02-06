"""Schemas for meeting operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    PrivacyLevel,
    TimeRangeMixin,
    TimezoneAwareDatetimeMixin,
)


class LogMeetingInput(BaseSchema, TimezoneAwareDatetimeMixin, TimeRangeMixin):
    """Input schema for logging a new meeting."""

    start_time: datetime = Field(
        description="Start time of meeting (timezone-aware)",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of meeting (timezone-aware)",
        examples=["2026-01-15T15:00:00-05:00"],
    )

    title: str = Field(
        description="Title of the meeting",
        min_length=1,
        max_length=255,
        examples=["Sprint Planning", "Client Kickoff"],
    )

    attendees: list[int] = Field(
        default_factory=list,
        description="List of person IDs who attended the meeting",
        examples=[[1, 2, 3], []],
    )

    project_id: int | None = Field(
        default=None,
        description="Optional project ID this meeting is related to",
        gt=0,
        examples=[1, 42],
    )

    description: str | None = Field(
        default=None,
        description="Optional notes or description of the meeting",
        max_length=2000,
        examples=["Discussed Q1 roadmap", "Reviewed architecture proposals"],
    )

    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE,
        description="Privacy level for this meeting",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags for categorization",
        examples=[["planning", "team"], ["client", "kickoff"]],
    )


class LogMeetingOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for logged meeting."""

    id: int = Field(
        description="Unique identifier for the meeting",
        examples=[1, 42],
    )

    start_time: datetime = Field(
        description="Start time of meeting",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of meeting",
        examples=["2026-01-15T15:00:00-05:00"],
    )

    title: str = Field(
        description="Title of the meeting",
        examples=["Sprint Planning"],
    )

    attendees: list[int] = Field(
        description="List of person IDs who attended",
        examples=[[1, 2, 3], []],
    )

    project_id: int | None = Field(
        default=None,
        description="Associated project ID if any",
    )

    description: str | None = Field(
        default=None,
        description="Meeting notes or description",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this meeting",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["planning", "team"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when meeting was created",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when meeting was last updated",
        examples=["2026-01-15T14:05:00-05:00"],
    )


class UpdateMeetingInput(BaseSchema, TimezoneAwareDatetimeMixin, TimeRangeMixin):
    """Input schema for updating an existing meeting."""

    start_time: datetime | None = Field(
        default=None,
        description="New start time (timezone-aware)",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    end_time: datetime | None = Field(
        default=None,
        description="New end time (timezone-aware)",
        examples=["2026-01-15T15:00:00-05:00"],
    )

    title: str | None = Field(
        default=None,
        description="New title",
        min_length=1,
        max_length=255,
        examples=["Updated Sprint Planning"],
    )

    attendees: list[int] | None = Field(
        default=None,
        description="New attendee list (replaces existing)",
        examples=[[1, 2, 3, 4]],
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
        examples=["Updated meeting notes"],
    )

    privacy_level: PrivacyLevel | None = Field(
        default=None,
        description="New privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["planning", "team", "updated"]],
    )


class UpdateMeetingOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated meeting."""

    id: int = Field(
        description="Unique identifier for the meeting",
        examples=[1, 42],
    )

    start_time: datetime = Field(
        description="Start time of meeting",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time of meeting",
        examples=["2026-01-15T15:00:00-05:00"],
    )

    title: str = Field(
        description="Title of the meeting",
        examples=["Sprint Planning"],
    )

    attendees: list[int] = Field(
        description="List of person IDs who attended",
        examples=[[1, 2, 3], []],
    )

    project_id: int | None = Field(
        default=None,
        description="Associated project ID if any",
    )

    description: str | None = Field(
        default=None,
        description="Meeting notes or description",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level of this meeting",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["planning", "team"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when meeting was created",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when meeting was last updated",
        examples=["2026-01-15T14:05:00-05:00"],
    )


class DeleteMeetingInput(BaseSchema):
    """Input schema for deleting a meeting."""

    meeting_id: int = Field(
        description="ID of the meeting to delete",
        gt=0,
        examples=[1, 42],
    )


class DeleteMeetingOutput(BaseSchema):
    """Output schema for deleted meeting confirmation."""

    success: bool = Field(
        description="Whether the deletion was successful",
        examples=[True],
    )

    message: str = Field(
        description="Human-readable confirmation message",
        examples=["Meeting deleted successfully"],
    )
