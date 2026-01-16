"""Unit tests for ResultConverter service."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.meeting import Meeting, MeetingAttendee
from src.mosaic.models.note import Note
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project, ProjectStatus
from src.mosaic.models.reminder import Reminder
from src.mosaic.models.user import User, WeekBoundary
from src.mosaic.models.work_session import WorkSession
from src.mosaic.schemas.query import (
    ClientResult,
    EmployerResult,
    MeetingResult,
    NoteResult,
    PersonResult,
    ProjectResult,
    ReminderResult,
    UserResult,
    WorkSessionResult,
)
from src.mosaic.services.result_converter import ResultConverter


class TestResultConverter:
    """Test result converter functionality."""

    @pytest.fixture
    def converter(self) -> ResultConverter:
        """Create a ResultConverter instance."""
        return ResultConverter()

    def test_convert_empty_results(self, converter: ResultConverter):
        """Test converting empty results."""
        raw_results = {
            "work_sessions": [],
            "meetings": [],
            "notes": [],
            "reminders": [],
            "projects": [],
            "people": [],
            "clients": [],
            "employers": [],
            "users": [],
        }

        results = converter.convert_results(raw_results)

        assert results == []
        assert isinstance(results, list)

    def test_convert_work_session(self, converter: ResultConverter):
        """Test converting a work session."""
        ws = WorkSession(
            id=1,
            project_id=10,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Implemented authentication",
            privacy_level=PrivacyLevel.PRIVATE,
            tags=["backend", "auth"],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )

        raw_results = {"work_sessions": [ws]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], WorkSessionResult)
        assert results[0].id == 1
        assert results[0].project_id == 10
        assert results[0].duration_hours == Decimal("3.0")
        assert results[0].description == "Implemented authentication"
        assert results[0].privacy_level == PrivacyLevel.PRIVATE
        assert results[0].tags == []  # WorkSession doesn't have tags yet

    def test_convert_work_session_without_tags(self, converter: ResultConverter):
        """Test converting a work session without tags."""
        ws = WorkSession(
            id=2,
            project_id=20,
            date=datetime(2024, 1, 16, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 15, 30, tzinfo=timezone.utc),
            duration_hours=Decimal("5.5"),
            summary="Bug fixes",
            privacy_level=PrivacyLevel.PUBLIC,
            created_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 15, 30, tzinfo=timezone.utc),
        )

        result = converter._convert_work_session(ws)

        assert result.id == 2
        assert result.tags == []
        assert result.privacy_level == PrivacyLevel.PUBLIC

    def test_convert_meeting_with_attendees(self, converter: ResultConverter):
        """Test converting a meeting with attendees."""
        meeting = Meeting(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=90,
            title="Sprint Planning",
            summary="Plan next sprint",
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["planning", "team"],
            project_id=10,
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc),
        )

        # Add attendees
        attendee1 = MeetingAttendee(meeting_id=1, person_id=100)
        attendee2 = MeetingAttendee(meeting_id=1, person_id=101)
        meeting.attendees = [attendee1, attendee2]

        raw_results = {"meetings": [meeting]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], MeetingResult)
        assert results[0].id == 1
        assert results[0].title == "Sprint Planning"
        assert results[0].description == "Plan next sprint"
        assert len(results[0].attendees) == 2
        assert 100 in results[0].attendees
        assert 101 in results[0].attendees
        assert results[0].project_id == 10
        assert results[0].tags == ["planning", "team"]
        # Check that end_time is calculated correctly (start + 90 minutes)
        expected_end = datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc)
        assert results[0].end_time == expected_end

    def test_convert_meeting_without_attendees(self, converter: ResultConverter):
        """Test converting a meeting without attendees."""
        meeting = Meeting(
            id=2,
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            duration_minutes=30,
            title="Daily Standup",
            summary="Team sync",
            privacy_level=PrivacyLevel.PRIVATE,
            tags=[],
            created_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 10, 30, tzinfo=timezone.utc),
        )
        meeting.attendees = []

        result = converter._convert_meeting(meeting)

        assert result.id == 2
        assert result.attendees == []
        assert result.project_id is None
        assert result.tags == []

    def test_convert_project(self, converter: ResultConverter):
        """Test converting a project."""
        project = Project(
            id=1,
            name="Website Redesign",
            client_id=50,
            status=ProjectStatus.ACTIVE,
            on_behalf_of_id=30,
            description="Redesign company website",
            tags=["web", "frontend", "high-priority"],
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        raw_results = {"projects": [project]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], ProjectResult)
        assert results[0].id == 1
        assert results[0].name == "Website Redesign"
        assert results[0].client_id == 50
        assert results[0].status == ProjectStatus.ACTIVE
        assert results[0].on_behalf_of == 30
        assert results[0].description == "Redesign company website"
        assert results[0].tags == ["web", "frontend", "high-priority"]

    def test_convert_project_minimal(self, converter: ResultConverter):
        """Test converting a project with minimal fields."""
        project = Project(
            id=2,
            name="Quick Fix",
            client_id=51,
            status=ProjectStatus.COMPLETED,
            created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )

        result = converter._convert_project(project)

        assert result.id == 2
        assert result.on_behalf_of is None
        assert result.description is None
        assert result.tags == []

    def test_convert_person(self, converter: ResultConverter):
        """Test converting a person."""
        person = Person(
            id=1,
            full_name="Jane Smith",
            email="jane@example.com",
            phone="+1-555-0123",
            company="TechCorp",
            title="Senior Engineer",
            notes="Met at conference",
            tags=["client", "technical"],
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        raw_results = {"people": [person]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], PersonResult)
        assert results[0].id == 1
        assert results[0].full_name == "Jane Smith"
        assert results[0].email == "jane@example.com"
        assert results[0].phone == "+1-555-0123"
        assert results[0].company == "TechCorp"
        assert results[0].title == "Senior Engineer"
        assert results[0].notes == "Met at conference"
        assert results[0].tags == ["client", "technical"]

    def test_convert_person_minimal(self, converter: ResultConverter):
        """Test converting a person with minimal fields."""
        person = Person(
            id=2,
            full_name="John Doe",
            created_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
        )

        result = converter._convert_person(person)

        assert result.id == 2
        assert result.full_name == "John Doe"
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title is None

    def test_convert_client(self, converter: ResultConverter):
        """Test converting a client."""
        client = Client(
            id=1,
            name="Acme Corporation",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            contact_person_id=100,
            notes="Long-term retainer",
            tags=["enterprise", "retainer"],
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        raw_results = {"clients": [client]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], ClientResult)
        assert results[0].id == 1
        assert results[0].name == "Acme Corporation"
        assert results[0].client_type == ClientType.COMPANY
        assert results[0].status == ClientStatus.ACTIVE
        assert results[0].contact_person_id == 100
        assert results[0].notes == "Long-term retainer"
        assert results[0].tags == ["enterprise", "retainer"]

    def test_convert_client_minimal(self, converter: ResultConverter):
        """Test converting a client with minimal fields."""
        client = Client(
            id=2,
            name="Smith Consulting",
            type=ClientType.INDIVIDUAL,
            status=ClientStatus.PAST,
            created_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
        )

        result = converter._convert_client(client)

        assert result.id == 2
        assert result.client_type == ClientType.INDIVIDUAL
        assert result.contact_person_id is None
        assert result.notes is None

    def test_convert_employer(self, converter: ResultConverter):
        """Test converting an employer."""
        employer = Employer(
            id=1,
            name="My Consulting LLC",
            notes="Primary business entity",
            tags=["primary", "consulting"],
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        raw_results = {"employers": [employer]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], EmployerResult)
        assert results[0].id == 1
        assert results[0].name == "My Consulting LLC"
        assert results[0].notes == "Primary business entity"
        assert results[0].tags == ["primary", "consulting"]

    def test_convert_employer_minimal(self, converter: ResultConverter):
        """Test converting an employer with minimal fields."""
        employer = Employer(
            id=2,
            name="Freelance",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        result = converter._convert_employer(employer)

        assert result.id == 2
        assert result.name == "Freelance"
        assert result.notes is None
        assert result.tags == []

    def test_convert_note(self, converter: ResultConverter):
        """Test converting a note."""
        note = Note(
            id=1,
            text="Follow up on proposal",
            entity_type=EntityType.PROJECT,
            entity_id=50,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["followup", "important"],
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        )

        raw_results = {"notes": [note]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], NoteResult)
        assert results[0].id == 1
        assert results[0].content == "Follow up on proposal"
        assert results[0].entity_type_attached == EntityType.PROJECT
        assert results[0].entity_id_attached == 50
        assert results[0].privacy_level == PrivacyLevel.INTERNAL
        assert results[0].tags == ["followup", "important"]

    def test_convert_note_standalone(self, converter: ResultConverter):
        """Test converting a standalone note without entity attachment."""
        note = Note(
            id=2,
            text="General reminder",
            entity_type=EntityType.WORK_SESSION,  # Required field in model
            entity_id=1,  # Required field in model
            privacy_level=PrivacyLevel.PRIVATE,
            tags=[],
            created_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
        )

        result = converter._convert_note(note)

        assert result.id == 2
        assert result.content == "General reminder"
        assert result.entity_type_attached == EntityType.WORK_SESSION
        assert result.entity_id_attached == 1

    def test_convert_reminder(self, converter: ResultConverter):
        """Test converting a reminder."""
        reminder = Reminder(
            id=1,
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Call client",
            related_entity_type=EntityType.PROJECT,
            related_entity_id=50,
            snoozed_until=datetime(2024, 1, 19, 10, 0, tzinfo=timezone.utc),
            tags=["urgent", "client"],
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 19, 10, 0, tzinfo=timezone.utc),
        )

        raw_results = {"reminders": [reminder]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], ReminderResult)
        assert results[0].id == 1
        assert results[0].reminder_time == datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc)
        assert results[0].message == "Call client"
        assert results[0].entity_type_attached == EntityType.PROJECT
        assert results[0].entity_id_attached == 50
        assert results[0].completed_at is None  # Model doesn't have completed_at
        assert results[0].snoozed_until == datetime(2024, 1, 19, 10, 0, tzinfo=timezone.utc)
        assert results[0].tags == ["urgent", "client"]

    def test_convert_reminder_without_entity(self, converter: ResultConverter):
        """Test converting a reminder without entity attachment."""
        reminder = Reminder(
            id=2,
            reminder_time=datetime(2024, 1, 21, 15, 0, tzinfo=timezone.utc),
            message="Team meeting",
            tags=[],
            created_at=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
        )

        result = converter._convert_reminder(reminder)

        assert result.id == 2
        assert result.entity_type_attached is None
        assert result.entity_id_attached is None
        assert result.snoozed_until is None

    def test_convert_user(self, converter: ResultConverter):
        """Test converting a user."""
        user = User(
            id=1,
            full_name="Test User",
            email="test@example.com",
            timezone="America/New_York",
            week_boundary=WeekBoundary.SUNDAY_SATURDAY,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

        raw_results = {"users": [user]}
        results = converter.convert_results(raw_results)

        assert len(results) == 1
        assert isinstance(results[0], UserResult)
        assert results[0].id == 1
        assert results[0].full_name == "Test User"
        assert results[0].email == "test@example.com"
        assert results[0].timezone == "America/New_York"
        assert results[0].week_boundary == WeekBoundary.SUNDAY_SATURDAY

    def test_convert_multiple_entity_types(self, converter: ResultConverter):
        """Test converting multiple entity types at once."""
        ws = WorkSession(
            id=1,
            project_id=10,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PRIVATE,
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )

        meeting = Meeting(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            title="Meeting",
            privacy_level=PrivacyLevel.PRIVATE,
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        )
        meeting.attendees = []

        person = Person(
            id=1,
            full_name="John Doe",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        raw_results = {
            "work_sessions": [ws],
            "meetings": [meeting],
            "people": [person],
            "projects": [],
            "clients": [],
            "employers": [],
            "notes": [],
            "reminders": [],
            "users": [],
        }

        results = converter.convert_results(raw_results)

        assert len(results) == 3
        assert isinstance(results[0], WorkSessionResult)
        assert isinstance(results[1], MeetingResult)
        assert isinstance(results[2], PersonResult)

    def test_convert_all_entity_types(self, converter: ResultConverter):
        """Test converting all entity types together."""
        ws = WorkSession(
            id=1,
            project_id=10,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PRIVATE,
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )

        meeting = Meeting(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            title="Meeting",
            privacy_level=PrivacyLevel.PRIVATE,
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        )
        meeting.attendees = []

        project = Project(
            id=1,
            name="Project",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        person = Person(
            id=1,
            full_name="John Doe",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        client = Client(
            id=1,
            name="Client",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        employer = Employer(
            id=1,
            name="Employer",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        note = Note(
            id=1,
            text="Note",
            entity_type=EntityType.PROJECT,
            entity_id=1,
            privacy_level=PrivacyLevel.PRIVATE,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        reminder = Reminder(
            id=1,
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Reminder",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        user = User(
            id=1,
            full_name="User",
            email="user@example.com",
            timezone="UTC",
            week_boundary=WeekBoundary.MONDAY_FRIDAY,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        raw_results = {
            "work_sessions": [ws],
            "meetings": [meeting],
            "projects": [project],
            "people": [person],
            "clients": [client],
            "employers": [employer],
            "notes": [note],
            "reminders": [reminder],
            "users": [user],
        }

        results = converter.convert_results(raw_results)

        assert len(results) == 9
        # Verify order: work_sessions, meetings, projects, people, clients,
        # employers, notes, reminders, users
        assert isinstance(results[0], WorkSessionResult)
        assert isinstance(results[1], MeetingResult)
        assert isinstance(results[2], ProjectResult)
        assert isinstance(results[3], PersonResult)
        assert isinstance(results[4], ClientResult)
        assert isinstance(results[5], EmployerResult)
        assert isinstance(results[6], NoteResult)
        assert isinstance(results[7], ReminderResult)
        assert isinstance(results[8], UserResult)
