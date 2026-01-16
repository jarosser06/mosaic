"""Schemas for person operations."""

from datetime import date, datetime

from pydantic import EmailStr, Field

from mosaic.schemas.common import (
    BaseSchema,
    DateRangeMixin,
    TimezoneAwareDatetimeMixin,
)


class AddPersonInput(BaseSchema):
    """Input schema for adding a new person."""

    full_name: str = Field(
        description="Full name of the person",
        min_length=1,
        max_length=255,
        examples=["John Doe", "Jane Smith"],
    )

    email: EmailStr | None = Field(
        default=None,
        description="Email address of the person",
        examples=["john.doe@example.com", "jane@company.com"],
    )

    phone: str | None = Field(
        default=None,
        description="Phone number of the person",
        max_length=50,
        examples=["+1-555-123-4567", "555-1234"],
    )

    company: str | None = Field(
        default=None,
        description="Company the person works for",
        max_length=255,
        examples=["Acme Corp", "Tech Solutions Inc"],
    )

    title: str | None = Field(
        default=None,
        description="Job title of the person",
        max_length=255,
        examples=["Senior Engineer", "Product Manager"],
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes about the person",
        max_length=2000,
        examples=["Met at conference 2025", "Prefers email communication"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["client", "technical"], ["colleague", "team"]],
    )


class AddPersonOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added person."""

    id: int = Field(
        description="Unique identifier for the person",
        examples=[1, 42],
    )

    full_name: str = Field(
        description="Full name of the person",
        examples=["John Doe"],
    )

    email: str | None = Field(
        default=None,
        description="Email address",
    )

    phone: str | None = Field(
        default=None,
        description="Phone number",
    )

    company: str | None = Field(
        default=None,
        description="Company name",
    )

    title: str | None = Field(
        default=None,
        description="Job title",
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["client", "technical"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when person was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when person was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdatePersonInput(BaseSchema):
    """Input schema for updating an existing person."""

    full_name: str | None = Field(
        default=None,
        description="New full name",
        min_length=1,
        max_length=255,
        examples=["John Doe Jr."],
    )

    email: EmailStr | None = Field(
        default=None,
        description="New email address",
        examples=["newemail@example.com"],
    )

    phone: str | None = Field(
        default=None,
        description="New phone number",
        max_length=50,
        examples=["+1-555-999-8888"],
    )

    company: str | None = Field(
        default=None,
        description="New company",
        max_length=255,
        examples=["New Company LLC"],
    )

    title: str | None = Field(
        default=None,
        description="New job title",
        max_length=255,
        examples=["Lead Engineer"],
    )

    notes: str | None = Field(
        default=None,
        description="New notes",
        max_length=2000,
        examples=["Updated contact information"],
    )

    tags: list[str] | None = Field(
        default=None,
        description="New tags (replaces existing tags)",
        examples=[["client", "technical", "active"]],
    )


class UpdatePersonOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for updated person."""

    id: int = Field(
        description="Unique identifier for the person",
        examples=[1, 42],
    )

    full_name: str = Field(
        description="Full name of the person",
        examples=["John Doe"],
    )

    email: str | None = Field(
        default=None,
        description="Email address",
    )

    phone: str | None = Field(
        default=None,
        description="Phone number",
    )

    company: str | None = Field(
        default=None,
        description="Company name",
    )

    title: str | None = Field(
        default=None,
        description="Job title",
    )

    notes: str | None = Field(
        default=None,
        description="Additional notes",
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["client", "technical"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when person was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when person was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class EmploymentHistoryInput(BaseSchema, DateRangeMixin):
    """Input schema for recording employment history."""

    person_id: int = Field(
        description="ID of the person",
        gt=0,
        examples=[1, 42],
    )

    employer_id: int = Field(
        description="ID of the employer",
        gt=0,
        examples=[1, 5],
    )

    start_date: date = Field(
        description="Start date of employment",
        examples=["2025-01-15", "2024-06-01"],
    )

    end_date: date | None = Field(
        default=None,
        description="End date of employment (null if currently employed)",
        examples=["2026-01-15", None],
    )

    title: str | None = Field(
        default=None,
        description="Job title during this employment period",
        max_length=255,
        examples=["Software Engineer", "Senior Developer"],
    )


class EmploymentHistoryOutput(BaseSchema):
    """Output schema for employment history record."""

    id: int = Field(
        description="Unique identifier for the employment history record",
        examples=[1, 42],
    )

    person_id: int = Field(
        description="ID of the person",
        examples=[1, 42],
    )

    employer_id: int = Field(
        description="ID of the employer",
        examples=[1, 5],
    )

    start_date: date = Field(
        description="Start date of employment",
        examples=["2025-01-15"],
    )

    end_date: date | None = Field(
        default=None,
        description="End date of employment",
    )

    title: str | None = Field(
        default=None,
        description="Job title",
    )
