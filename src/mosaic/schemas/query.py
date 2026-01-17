"""Schemas for natural language query operations with discriminated unions."""

import datetime as dt
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    TimezoneAwareDatetimeMixin,
    WeekBoundary,
)


class QueryInput(BaseSchema):
    """Input schema for natural language queries."""

    query: str = Field(
        description="Natural language query about work history",
        min_length=1,
        max_length=2000,
        examples=[
            "How many hours did I work last week?",
            "Show me all meetings with John from Acme Corp",
            "What projects am I currently working on?",
        ],
    )


# Entity result schemas (for discriminated union)


class WorkSessionResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Work session query result."""

    entity_type: Literal["work_session"] = Field(
        default="work_session",
        description="Entity type discriminator",
    )

    id: int = Field(description="Work session ID", examples=[1, 42])

    date: dt.date = Field(
        description="Work session date",
        examples=["2026-01-15"],
    )

    start_time: datetime = Field(
        description="Start time",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time",
        examples=["2026-01-15T17:30:00-05:00"],
    )

    project_id: int = Field(description="Project ID", examples=[1, 42])

    duration_hours: Decimal = Field(
        description="Duration in hours",
        examples=[8.5, 4.0],
    )

    description: str | None = Field(
        default=None,
        description="Work description",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["backend", "api"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T09:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T09:05:00-05:00"],
    )


class MeetingResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Meeting query result."""

    entity_type: Literal["meeting"] = Field(
        default="meeting",
        description="Entity type discriminator",
    )

    id: int = Field(description="Meeting ID", examples=[1, 42])

    start_time: datetime = Field(
        description="Start time",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    end_time: datetime = Field(
        description="End time",
        examples=["2026-01-15T15:00:00-05:00"],
    )

    title: str = Field(description="Meeting title", examples=["Sprint Planning"])

    attendees: list[int] = Field(
        description="Attendee person IDs",
        examples=[[1, 2, 3], []],
    )

    project_id: int | None = Field(
        default=None,
        description="Associated project ID",
    )

    description: str | None = Field(
        default=None,
        description="Meeting description",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["planning", "team"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T14:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T14:05:00-05:00"],
    )


class PersonResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Person query result."""

    entity_type: Literal["person"] = Field(
        default="person",
        description="Entity type discriminator",
    )

    id: int = Field(description="Person ID", examples=[1, 42])

    full_name: str = Field(description="Full name", examples=["John Doe"])

    email: str | None = Field(default=None, description="Email address")

    phone: str | None = Field(default=None, description="Phone number")

    company: str | None = Field(default=None, description="Company name")

    title: str | None = Field(default=None, description="Job title")

    notes: str | None = Field(default=None, description="Notes")

    tags: list[str] = Field(
        description="Tags",
        examples=[["client", "technical"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class ClientResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Client query result."""

    entity_type: Literal["client"] = Field(
        default="client",
        description="Entity type discriminator",
    )

    id: int = Field(description="Client ID", examples=[1, 42])

    name: str = Field(description="Client name", examples=["Acme Corporation"])

    client_type: ClientType = Field(
        description="Client type",
        examples=["company", "individual"],
    )

    status: ClientStatus = Field(
        description="Client status",
        examples=["active", "past"],
    )

    contact_person_id: int | None = Field(
        default=None,
        description="Primary contact person ID",
    )

    notes: str | None = Field(default=None, description="Notes")

    tags: list[str] = Field(
        description="Tags",
        examples=[["enterprise", "long-term"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class ProjectResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Project query result."""

    entity_type: Literal["project"] = Field(
        default="project",
        description="Entity type discriminator",
    )

    id: int = Field(description="Project ID", examples=[1, 42])

    name: str = Field(description="Project name", examples=["Website Redesign"])

    client_id: int = Field(description="Client ID", examples=[1, 42])

    status: ProjectStatus = Field(
        description="Project status",
        examples=["active", "paused", "completed"],
    )

    on_behalf_of: int | None = Field(
        default=None,
        description="Employer/client ID for work attribution",
    )

    description: str | None = Field(default=None, description="Project description")

    tags: list[str] = Field(
        description="Tags",
        examples=[["web", "frontend"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class EmployerResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Employer query result."""

    entity_type: Literal["employer"] = Field(
        default="employer",
        description="Entity type discriminator",
    )

    id: int = Field(description="Employer ID", examples=[1, 42])

    name: str = Field(description="Employer name", examples=["Tech Corp"])

    notes: str | None = Field(default=None, description="Notes")

    tags: list[str] = Field(
        description="Tags",
        examples=[["technology", "remote"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class NoteResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Note query result."""

    entity_type: Literal["note"] = Field(
        default="note",
        description="Entity type discriminator",
    )

    id: int = Field(description="Note ID", examples=[1, 42])

    content: str = Field(
        description="Note content",
        examples=["Remember to follow up on proposal"],
    )

    entity_type_attached: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id_attached: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["important", "follow-up"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class ReminderResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """Reminder query result."""

    entity_type: Literal["reminder"] = Field(
        default="reminder",
        description="Entity type discriminator",
    )

    id: int = Field(description="Reminder ID", examples=[1, 42])

    reminder_time: datetime = Field(
        description="Reminder time",
        examples=["2026-01-20T09:00:00-05:00"],
    )

    message: str = Field(
        description="Reminder message",
        examples=["Call client about project status"],
    )

    entity_type_attached: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id_attached: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    is_completed: bool = Field(
        default=False,
        description="Whether reminder is completed",
    )

    snoozed_until: datetime | None = Field(
        default=None,
        description="Snoozed until timestamp",
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["urgent", "call"], []],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UserResult(BaseSchema, TimezoneAwareDatetimeMixin):
    """User query result."""

    entity_type: Literal["user"] = Field(
        default="user",
        description="Entity type discriminator",
    )

    id: int = Field(description="User ID", examples=[1])

    full_name: str = Field(description="Full name", examples=["John Doe"])

    email: str | None = Field(
        default=None,
        description="Email address",
        examples=["john.doe@example.com"],
    )

    timezone: str = Field(
        description="Timezone",
        examples=["America/New_York", "UTC"],
    )

    week_boundary: WeekBoundary = Field(
        description="Week boundary preference",
        examples=["mon-fri", "sun-sat", "mon-sun"],
    )

    created_at: datetime = Field(
        description="Created timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Updated timestamp",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class EmploymentHistoryResult(BaseSchema):
    """Employment history query result."""

    entity_type: Literal["employment_history"] = Field(
        default="employment_history",
        description="Entity type discriminator",
    )

    id: int = Field(description="Employment history ID", examples=[1, 42])

    person_id: int = Field(description="Person ID", examples=[1, 42])

    employer_id: int = Field(description="Employer ID", examples=[1, 5])

    start_date: dt.date = Field(
        description="Start date",
        examples=["2025-01-15"],
    )

    end_date: dt.date | None = Field(
        default=None,
        description="End date (null if current)",
    )

    title: str | None = Field(default=None, description="Job title")


# Discriminated union for query results
QueryResultEntity = Annotated[
    WorkSessionResult
    | MeetingResult
    | PersonResult
    | ClientResult
    | ProjectResult
    | EmployerResult
    | NoteResult
    | ReminderResult
    | UserResult
    | EmploymentHistoryResult,
    Field(discriminator="entity_type"),
]


class QueryOutput(BaseSchema):
    """Output schema for query results with discriminated union."""

    summary: str = Field(
        description="Natural language summary of query results",
        examples=[
            "Found 5 work sessions last week totaling 42.5 hours",
            "You have 3 active projects",
        ],
    )

    results: list[QueryResultEntity] = Field(
        description="List of matching entities (discriminated union)",
        examples=[[]],
    )

    total_count: int = Field(
        description="Total number of results",
        ge=0,
        examples=[5, 0, 100],
    )
