"""Base models, enums, and mixins for all database entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PrivacyLevel(str, Enum):
    """Privacy levels for work sessions, meetings, and notes."""

    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


class WeekBoundary(str, Enum):
    """Week boundary definitions for timecard generation."""

    MONDAY_FRIDAY = "mon-fri"
    SUNDAY_SATURDAY = "sun-sat"
    MONDAY_SUNDAY = "mon-sun"


class EntityType(str, Enum):
    """Entity types for note and reminder attachments."""

    PERSON = "person"
    CLIENT = "client"
    PROJECT = "project"
    EMPLOYER = "employer"
    WORK_SESSION = "work_session"
    MEETING = "meeting"
    NOTE = "note"
    REMINDER = "reminder"


class ProjectStatus(str, Enum):
    """Status for projects."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ClientStatus(str, Enum):
    """Status for clients."""

    ACTIVE = "active"
    PAST = "past"


class ClientType(str, Enum):
    """Type of client entity."""

    COMPANY = "company"
    INDIVIDUAL = "individual"


class Base(DeclarativeBase):
    """Base class for all database models."""

    type_annotation_map = {
        dict[str, Any]: "JSONB",
    }


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
