"""Schemas for notification operations."""

from pydantic import Field

from mosaic.schemas.common import BaseSchema


class TriggerNotificationInput(BaseSchema):
    """Input schema for triggering a macOS notification."""

    title: str = Field(
        description="Notification title",
        min_length=1,
        max_length=255,
        examples=["Reminder", "Meeting Starting Soon"],
    )

    message: str = Field(
        description="Notification message body",
        min_length=1,
        max_length=1000,
        examples=[
            "Don't forget to submit timesheet",
            "Sprint planning meeting in 5 minutes",
        ],
    )


class TriggerNotificationOutput(BaseSchema):
    """Output schema for triggered notification."""

    success: bool = Field(
        description="Whether the notification was successfully triggered",
        examples=[True, False],
    )

    message: str = Field(
        description="Status message describing the result",
        examples=[
            "Notification sent successfully",
            "Failed to reach notification bridge",
        ],
    )
