"""Database models for Mosaic."""

from .base import (
    Base,
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    TimestampMixin,
    WeekBoundary,
)
from .client import Client
from .employer import Employer
from .meeting import Meeting, MeetingAttendee
from .note import Note
from .person import EmploymentHistory, Person
from .project import Project
from .reminder import Reminder
from .user import User
from .work_session import WorkSession

__all__ = [
    # Base classes and enums
    "Base",
    "TimestampMixin",
    "PrivacyLevel",
    "WeekBoundary",
    "EntityType",
    "ProjectStatus",
    "ClientStatus",
    "ClientType",
    # Models
    "User",
    "Employer",
    "Client",
    "Person",
    "EmploymentHistory",
    "Project",
    "WorkSession",
    "Meeting",
    "MeetingAttendee",
    "Reminder",
    "Note",
]
