"""Database models for Mosaic."""

from .action_item import ActionItem
from .base import (
    ActionItemStatus,
    Base,
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    TimestampMixin,
    WeekBoundary,
)
from .bookmark import Bookmark
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
    "ActionItemStatus",
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
    "ActionItem",
    "Bookmark",
]
