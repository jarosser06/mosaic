"""Schemas for user profile operations."""

from datetime import datetime

from pydantic import EmailStr, Field

from mosaic.schemas.common import BaseSchema, TimezoneAwareDatetimeMixin


class UpdateUserInput(BaseSchema):
    """Input schema for updating user profile."""

    full_name: str | None = Field(
        default=None,
        description="Full name",
        min_length=1,
        max_length=255,
        examples=["John Doe", "Jane Smith"],
    )

    email: EmailStr | None = Field(
        default=None,
        description="Email address",
        examples=["john.doe@example.com"],
    )

    phone: str | None = Field(
        default=None,
        description="Phone number",
        max_length=50,
        examples=["+1-555-123-4567", "555-1234"],
    )

    timezone: str | None = Field(
        default=None,
        description="IANA timezone string",
        examples=["America/New_York", "Europe/London", "UTC"],
    )

    week_boundary: str | None = Field(
        default=None,
        description=(
            "Week boundary preference "
            "(monday_friday, sunday_saturday, monday_sunday, sunday_thursday)"
        ),
        examples=["monday_friday", "sunday_saturday"],
    )

    working_hours_start: int | None = Field(
        default=None,
        description="Work day start hour (24h format, 0-23)",
        ge=0,
        le=23,
        examples=[9, 8],
    )

    working_hours_end: int | None = Field(
        default=None,
        description="Work day end hour (24h format, 0-23)",
        ge=0,
        le=23,
        examples=[17, 18],
    )

    communication_style: str | None = Field(
        default=None,
        description="Preferred communication style and preferences for authenticity",
        max_length=1000,
        examples=["Direct and concise, prefer bullet points over long paragraphs"],
    )

    work_approach: str | None = Field(
        default=None,
        description="Work approach, values, and methodology",
        max_length=1000,
        examples=["Agile mindset, test-driven development, continuous learning"],
    )


class UpdateUserOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated user profile."""

    id: int = Field(
        description="Unique identifier for the user",
        examples=[1],
    )

    full_name: str = Field(
        description="Full name",
        examples=["John Doe"],
    )

    email: str | None = Field(
        description="Email address",
        examples=["john.doe@example.com"],
    )

    phone: str | None = Field(
        description="Phone number",
        examples=["+1-555-123-4567"],
    )

    timezone: str = Field(
        description="IANA timezone",
        examples=["America/New_York", "UTC"],
    )

    week_boundary: str = Field(
        description="Week boundary",
        examples=["monday_friday"],
    )

    working_hours_start: int | None = Field(
        description="Work day start hour",
        examples=[9],
    )

    working_hours_end: int | None = Field(
        description="Work day end hour",
        examples=[17],
    )

    communication_style: str | None = Field(
        description="Communication style preferences",
        examples=["Direct and concise"],
    )

    work_approach: str | None = Field(
        description="Work approach and values",
        examples=["Agile, TDD"],
    )

    profile_last_updated: datetime | None = Field(
        description="When profile was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    created_at: datetime = Field(
        description="When user was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="When user was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class GetUserOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for getting user profile."""

    id: int | None = Field(
        description="Unique identifier (None if not initialized)",
        examples=[1],
    )

    full_name: str = Field(
        description="Full name",
        examples=["John Doe", ""],
    )

    email: str | None = Field(
        description="Email address",
        examples=["john.doe@example.com"],
    )

    phone: str | None = Field(
        description="Phone number",
        examples=["+1-555-123-4567"],
    )

    timezone: str = Field(
        description="IANA timezone",
        examples=["America/New_York", "UTC"],
    )

    week_boundary: str = Field(
        description="Week boundary",
        examples=["monday_friday"],
    )

    working_hours_start: int | None = Field(
        description="Work day start hour",
        examples=[9],
    )

    working_hours_end: int | None = Field(
        description="Work day end hour",
        examples=[17],
    )

    communication_style: str | None = Field(
        description="Communication style preferences",
        examples=["Direct and concise"],
    )

    work_approach: str | None = Field(
        description="Work approach and values",
        examples=["Agile, TDD"],
    )

    profile_last_updated: datetime | None = Field(
        description="When profile was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    created_at: datetime | None = Field(
        description="When user was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime | None = Field(
        description="When user was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )
