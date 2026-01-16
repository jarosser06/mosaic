"""Result converter service for query results."""

from typing import Any

from ..models.client import Client
from ..models.employer import Employer
from ..models.meeting import Meeting
from ..models.note import Note
from ..models.person import Person
from ..models.project import Project
from ..models.reminder import Reminder
from ..models.user import User
from ..models.work_session import WorkSession
from ..schemas.query import (
    ClientResult,
    EmployerResult,
    MeetingResult,
    NoteResult,
    PersonResult,
    ProjectResult,
    QueryResultEntity,
    ReminderResult,
    UserResult,
    WorkSessionResult,
)


class ResultConverter:
    """
    Convert SQLAlchemy model instances to QueryResultEntity schemas.

    Handles discriminated union conversion for all entity types
    returned by QueryService.flexible_query().
    """

    def convert_results(self, raw_results: dict[str, list[Any]]) -> list[QueryResultEntity]:
        """
        Convert SQLAlchemy results to QueryResultEntity discriminated union.

        Args:
            raw_results: Results from QueryService.flexible_query()
                Keys: "work_sessions", "meetings", "notes", "reminders",
                      "projects", "people", "clients", "employers", "users"
                Values: Lists of SQLAlchemy model instances

        Returns:
            list[QueryResultEntity]: Flattened list of converted results

        Examples:
            >>> converter = ResultConverter()
            >>> raw = {"work_sessions": [ws1, ws2], "meetings": [m1]}
            >>> results = converter.convert_results(raw)
            >>> len(results)
            3
        """
        converted: list[QueryResultEntity] = []

        # Convert work sessions
        for ws in raw_results.get("work_sessions", []):
            converted.append(self._convert_work_session(ws))

        # Convert meetings
        for meeting in raw_results.get("meetings", []):
            converted.append(self._convert_meeting(meeting))

        # Convert projects
        for project in raw_results.get("projects", []):
            converted.append(self._convert_project(project))

        # Convert people
        for person in raw_results.get("people", []):
            converted.append(self._convert_person(person))

        # Convert clients
        for client in raw_results.get("clients", []):
            converted.append(self._convert_client(client))

        # Convert employers
        for employer in raw_results.get("employers", []):
            converted.append(self._convert_employer(employer))

        # Convert notes
        for note in raw_results.get("notes", []):
            converted.append(self._convert_note(note))

        # Convert reminders
        for reminder in raw_results.get("reminders", []):
            converted.append(self._convert_reminder(reminder))

        # Convert users
        for user in raw_results.get("users", []):
            converted.append(self._convert_user(user))

        return converted

    def _convert_work_session(self, ws: WorkSession) -> WorkSessionResult:
        """
        Convert WorkSession model to WorkSessionResult schema.

        Args:
            ws: WorkSession model instance

        Returns:
            WorkSessionResult: Pydantic schema instance
        """
        return WorkSessionResult(
            id=ws.id,
            start_time=ws.start_time,
            end_time=ws.end_time,
            project_id=ws.project_id,
            duration_hours=ws.duration_hours,
            description=ws.summary,
            privacy_level=ws.privacy_level,
            tags=[],  # WorkSession model doesn't have tags field yet
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        )

    def _convert_meeting(self, meeting: Meeting) -> MeetingResult:
        """
        Convert Meeting model to MeetingResult schema.

        Args:
            meeting: Meeting model instance

        Returns:
            MeetingResult: Pydantic schema instance
        """
        from datetime import timedelta

        # Extract attendee IDs from relationship
        attendee_ids = [attendee.person_id for attendee in meeting.attendees]

        # Calculate end_time from start_time + duration_minutes
        end_time = meeting.start_time + timedelta(minutes=meeting.duration_minutes)

        return MeetingResult(
            id=meeting.id,
            start_time=meeting.start_time,
            end_time=end_time,
            title=meeting.title,
            attendees=attendee_ids,
            project_id=meeting.project_id,
            description=meeting.summary,
            privacy_level=meeting.privacy_level,
            tags=meeting.tags or [],
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
        )

    def _convert_project(self, project: Project) -> ProjectResult:
        """
        Convert Project model to ProjectResult schema.

        Args:
            project: Project model instance

        Returns:
            ProjectResult: Pydantic schema instance
        """
        return ProjectResult(
            id=project.id,
            name=project.name,
            client_id=project.client_id,
            status=project.status,
            on_behalf_of=project.on_behalf_of_id,
            description=project.description,
            tags=project.tags or [],
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def _convert_person(self, person: Person) -> PersonResult:
        """
        Convert Person model to PersonResult schema.

        Args:
            person: Person model instance

        Returns:
            PersonResult: Pydantic schema instance
        """
        return PersonResult(
            id=person.id,
            full_name=person.full_name,
            email=person.email,
            phone=person.phone,
            company=person.company,
            title=person.title,
            notes=person.notes,
            tags=person.tags or [],
            created_at=person.created_at,
            updated_at=person.updated_at,
        )

    def _convert_client(self, client: Client) -> ClientResult:
        """
        Convert Client model to ClientResult schema.

        Args:
            client: Client model instance

        Returns:
            ClientResult: Pydantic schema instance
        """
        return ClientResult(
            id=client.id,
            name=client.name,
            client_type=client.type,  # Client model uses 'type' not 'client_type'
            status=client.status,
            contact_person_id=client.contact_person_id,
            notes=client.notes,
            tags=client.tags or [],
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    def _convert_employer(self, employer: Employer) -> EmployerResult:
        """
        Convert Employer model to EmployerResult schema.

        Args:
            employer: Employer model instance

        Returns:
            EmployerResult: Pydantic schema instance
        """
        return EmployerResult(
            id=employer.id,
            name=employer.name,
            notes=employer.notes,
            tags=employer.tags or [],
            created_at=employer.created_at,
            updated_at=employer.updated_at,
        )

    def _convert_note(self, note: Note) -> NoteResult:
        """
        Convert Note model to NoteResult schema.

        Args:
            note: Note model instance

        Returns:
            NoteResult: Pydantic schema instance
        """
        return NoteResult(
            id=note.id,
            content=note.text,
            entity_type_attached=note.entity_type,
            entity_id_attached=note.entity_id,
            privacy_level=note.privacy_level,
            tags=note.tags or [],
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    def _convert_reminder(self, reminder: Reminder) -> ReminderResult:
        """
        Convert Reminder model to ReminderResult schema.

        Args:
            reminder: Reminder model instance

        Returns:
            ReminderResult: Pydantic schema instance
        """
        return ReminderResult(
            id=reminder.id,
            reminder_time=reminder.reminder_time,  # Reminder model uses 'reminder_time'
            message=reminder.message,  # Reminder model uses 'message' not 'text'
            entity_type_attached=reminder.related_entity_type,
            entity_id_attached=reminder.related_entity_id,
            completed_at=None,  # Reminder model doesn't have completed_at field
            snoozed_until=reminder.snoozed_until,
            tags=reminder.tags or [],
            created_at=reminder.created_at,
            updated_at=reminder.updated_at,
        )

    def _convert_user(self, user: User) -> UserResult:
        """
        Convert User model to UserResult schema.

        Args:
            user: User model instance

        Returns:
            UserResult: Pydantic schema instance
        """
        return UserResult(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            timezone=user.timezone,
            week_boundary=user.week_boundary,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
