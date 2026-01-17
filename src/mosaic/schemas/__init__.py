"""Pydantic schemas for MCP tool input/output validation."""

from mosaic.schemas.client import (
    AddClientInput,
    AddClientOutput,
    UpdateClientInput,
    UpdateClientOutput,
)
from mosaic.schemas.common import (
    BaseSchema,
    ClientStatus,
    ClientType,
    DateRangeMixin,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    TimeRangeMixin,
    TimezoneAwareDatetimeMixin,
    WeekBoundary,
)
from mosaic.schemas.employer import AddEmployerInput, AddEmployerOutput
from mosaic.schemas.meeting import (
    LogMeetingInput,
    LogMeetingOutput,
    UpdateMeetingInput,
    UpdateMeetingOutput,
)
from mosaic.schemas.note import (
    AddNoteInput,
    AddNoteOutput,
    UpdateNoteInput,
    UpdateNoteOutput,
)
from mosaic.schemas.notification import (
    TriggerNotificationInput,
    TriggerNotificationOutput,
)
from mosaic.schemas.person import (
    AddPersonInput,
    AddPersonOutput,
    EmploymentHistoryInput,
    EmploymentHistoryOutput,
    UpdatePersonInput,
    UpdatePersonOutput,
)
from mosaic.schemas.project import (
    AddProjectInput,
    AddProjectOutput,
    UpdateProjectInput,
    UpdateProjectOutput,
)
from mosaic.schemas.prompts import (
    FindGapsArgs,
    GenerateTimecardArgs,
    SearchContextArgs,
    WeeklyReviewArgs,
)
from mosaic.schemas.query import (
    ClientResult,
    EmployerResult,
    EmploymentHistoryResult,
    MeetingResult,
    NoteResult,
    PersonResult,
    ProjectResult,
    QueryInput,
    QueryOutput,
    QueryResultEntity,
    ReminderResult,
    UserResult,
    WorkSessionResult,
)
from mosaic.schemas.query_structured import (
    AggregationFunction,
    AggregationResult,
    AggregationSpec,
    FilterOperator,
    FilterSpec,
    StructuredQueryInput,
    StructuredQueryOutput,
)
from mosaic.schemas.reminder import (
    AddReminderInput,
    AddReminderOutput,
    CompleteReminderInput,
    CompleteReminderOutput,
    SnoozeReminderInput,
    SnoozeReminderOutput,
)
from mosaic.schemas.user import GetUserOutput, UpdateUserInput, UpdateUserOutput
from mosaic.schemas.work_session import (
    LogWorkSessionInput,
    LogWorkSessionOutput,
    UpdateWorkSessionInput,
    UpdateWorkSessionOutput,
)

__all__ = [
    # Common
    "BaseSchema",
    "TimezoneAwareDatetimeMixin",
    "TimeRangeMixin",
    "DateRangeMixin",
    # Enums
    "PrivacyLevel",
    "WeekBoundary",
    "EntityType",
    "ProjectStatus",
    "ClientStatus",
    "ClientType",
    # Work Session
    "LogWorkSessionInput",
    "LogWorkSessionOutput",
    "UpdateWorkSessionInput",
    "UpdateWorkSessionOutput",
    # Meeting
    "LogMeetingInput",
    "LogMeetingOutput",
    "UpdateMeetingInput",
    "UpdateMeetingOutput",
    # Person
    "AddPersonInput",
    "AddPersonOutput",
    "UpdatePersonInput",
    "UpdatePersonOutput",
    "EmploymentHistoryInput",
    "EmploymentHistoryOutput",
    # Client
    "AddClientInput",
    "AddClientOutput",
    "UpdateClientInput",
    "UpdateClientOutput",
    # Project
    "AddProjectInput",
    "AddProjectOutput",
    "UpdateProjectInput",
    "UpdateProjectOutput",
    # Employer
    "AddEmployerInput",
    "AddEmployerOutput",
    # Note
    "AddNoteInput",
    "AddNoteOutput",
    "UpdateNoteInput",
    "UpdateNoteOutput",
    # Reminder
    "AddReminderInput",
    "AddReminderOutput",
    "CompleteReminderInput",
    "CompleteReminderOutput",
    "SnoozeReminderInput",
    "SnoozeReminderOutput",
    # User
    "UpdateUserProfileInput",
    "UpdateUserProfileOutput",
    # Query
    "QueryInput",
    "QueryOutput",
    "QueryResultEntity",
    "WorkSessionResult",
    "MeetingResult",
    "PersonResult",
    "ClientResult",
    "ProjectResult",
    "EmployerResult",
    "NoteResult",
    "ReminderResult",
    "UserResult",
    "EmploymentHistoryResult",
    # Structured Query
    "FilterOperator",
    "FilterSpec",
    "AggregationFunction",
    "AggregationSpec",
    "StructuredQueryInput",
    "AggregationResult",
    "StructuredQueryOutput",
    # Notification
    "TriggerNotificationInput",
    "TriggerNotificationOutput",
    # Prompts
    "GenerateTimecardArgs",
    "WeeklyReviewArgs",
    "FindGapsArgs",
    "SearchContextArgs",
    # User
    "GetUserOutput",
    "UpdateUserInput",
    "UpdateUserOutput",
]
