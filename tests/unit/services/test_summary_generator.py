"""Unit tests for SummaryGenerator service."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.mosaic.models.base import EntityType, PrivacyLevel, ProjectStatus
from src.mosaic.models.client import ClientStatus, ClientType
from src.mosaic.schemas.common import WeekBoundary
from src.mosaic.schemas.query import (
    ClientResult,
    EmployerResult,
    EmploymentHistoryResult,
    MeetingResult,
    NoteResult,
    PersonResult,
    ProjectResult,
    ReminderResult,
    UserResult,
    WorkSessionResult,
)
from src.mosaic.services.summary_generator import SummaryGenerator


class TestSummaryGenerator:
    """Test summary generator functionality."""

    @pytest.fixture
    def generator(self) -> SummaryGenerator:
        """Create a SummaryGenerator instance."""
        return SummaryGenerator()

    def test_generate_empty_results(self, generator: SummaryGenerator):
        """Test generating summary with no results."""
        summary = generator.generate([], include_private=True)
        assert summary == "No results found."

    def test_generate_all_private_excluded(self, generator: SummaryGenerator):
        """Test generating summary when all results are private and excluded."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Private work",
            privacy_level=PrivacyLevel.PRIVATE,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws], include_private=False)
        assert summary == "No results found (all results are private)."

    def test_generate_single_work_session(self, generator: SummaryGenerator):
        """Test generating summary with one work session."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Implemented feature",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["backend"],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws], include_private=True)
        assert summary == "Found 1 work session (3.0 hours)."

    def test_generate_multiple_work_sessions(self, generator: SummaryGenerator):
        """Test generating summary with multiple work sessions."""
        ws1 = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work 1",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        ws2 = WorkSessionResult(
            id=2,
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 14, 30, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("5.5"),
            description="Work 2",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws1, ws2], include_private=True)
        assert summary == "Found 2 work sessions (8.5 hours)."

    def test_generate_work_session_with_privacy_filtering(self, generator: SummaryGenerator):
        """Test work session summary respects privacy filtering."""
        ws_public = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Public work",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        ws_private = WorkSessionResult(
            id=2,
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 14, 30, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("5.5"),
            description="Private work",
            privacy_level=PrivacyLevel.PRIVATE,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        # Include private
        summary_all = generator.generate([ws_public, ws_private], include_private=True)
        assert summary_all == "Found 2 work sessions (8.5 hours)."

        # Exclude private
        summary_public = generator.generate([ws_public, ws_private], include_private=False)
        assert summary_public == "Found 1 work session (3.0 hours)."

    def test_generate_single_meeting(self, generator: SummaryGenerator):
        """Test generating summary with one meeting."""
        meeting = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Sprint Planning",
            attendees=[1, 2],
            project_id=1,
            description="Plan next sprint",
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["planning"],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([meeting], include_private=True)
        assert summary == "Found 1 meeting."

    def test_generate_multiple_meetings(self, generator: SummaryGenerator):
        """Test generating summary with multiple meetings."""
        meeting1 = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting 1",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        meeting2 = MeetingResult(
            id=2,
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 11, 0, tzinfo=timezone.utc),
            title="Meeting 2",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([meeting1, meeting2], include_private=True)
        assert summary == "Found 2 meetings."

    def test_generate_work_sessions_and_meetings(self, generator: SummaryGenerator):
        """Test generating summary with work sessions and meetings."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        meeting = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws, meeting], include_private=True)
        assert summary == "Found 1 work session (3.0 hours) and 1 meeting."

    def test_generate_single_project(self, generator: SummaryGenerator):
        """Test generating summary with one project."""
        project = ProjectResult(
            id=1,
            name="Test Project",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([project], include_private=True)
        assert summary == "Found 1 project."

    def test_generate_multiple_projects(self, generator: SummaryGenerator):
        """Test generating summary with multiple projects."""
        project1 = ProjectResult(
            id=1,
            name="Project 1",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        project2 = ProjectResult(
            id=2,
            name="Project 2",
            client_id=1,
            status=ProjectStatus.COMPLETED,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([project1, project2], include_private=True)
        assert summary == "Found 2 projects."

    def test_generate_single_person(self, generator: SummaryGenerator):
        """Test generating summary with one person."""
        person = PersonResult(
            id=1,
            full_name="John Doe",
            email="john@example.com",
            phone=None,
            company=None,
            title=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([person], include_private=True)
        assert summary == "Found 1 person."

    def test_generate_multiple_people(self, generator: SummaryGenerator):
        """Test generating summary with multiple people."""
        person1 = PersonResult(
            id=1,
            full_name="John Doe",
            email="john@example.com",
            phone=None,
            company=None,
            title=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        person2 = PersonResult(
            id=2,
            full_name="Jane Smith",
            email="jane@example.com",
            phone=None,
            company=None,
            title=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([person1, person2], include_private=True)
        assert summary == "Found 2 people."

    def test_generate_single_client(self, generator: SummaryGenerator):
        """Test generating summary with one client."""
        client = ClientResult(
            id=1,
            name="Acme Corp",
            client_type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            contact_person_id=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([client], include_private=True)
        assert summary == "Found 1 client."

    def test_generate_multiple_clients(self, generator: SummaryGenerator):
        """Test generating summary with multiple clients."""
        client1 = ClientResult(
            id=1,
            name="Client 1",
            client_type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            contact_person_id=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        client2 = ClientResult(
            id=2,
            name="Client 2",
            client_type=ClientType.INDIVIDUAL,
            status=ClientStatus.PAST,
            contact_person_id=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([client1, client2], include_private=True)
        assert summary == "Found 2 clients."

    def test_generate_single_employer(self, generator: SummaryGenerator):
        """Test generating summary with one employer."""
        employer = EmployerResult(
            id=1,
            name="My Company LLC",
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([employer], include_private=True)
        assert summary == "Found 1 employer."

    def test_generate_multiple_employers(self, generator: SummaryGenerator):
        """Test generating summary with multiple employers."""
        employer1 = EmployerResult(
            id=1,
            name="Company 1",
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        employer2 = EmployerResult(
            id=2,
            name="Company 2",
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([employer1, employer2], include_private=True)
        assert summary == "Found 2 employers."

    def test_generate_single_note(self, generator: SummaryGenerator):
        """Test generating summary with one note."""
        note = NoteResult(
            id=1,
            content="Important note",
            entity_type_attached=None,
            entity_id_attached=None,
            privacy_level=PrivacyLevel.PRIVATE,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([note], include_private=True)
        assert summary == "Found 1 note."

    def test_generate_multiple_notes(self, generator: SummaryGenerator):
        """Test generating summary with multiple notes."""
        note1 = NoteResult(
            id=1,
            content="Note 1",
            entity_type_attached=None,
            entity_id_attached=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        note2 = NoteResult(
            id=2,
            content="Note 2",
            entity_type_attached=EntityType.PROJECT,
            entity_id_attached=1,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([note1, note2], include_private=True)
        assert summary == "Found 2 notes."

    def test_generate_single_reminder(self, generator: SummaryGenerator):
        """Test generating summary with one reminder."""
        reminder = ReminderResult(
            id=1,
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Call client",
            entity_type_attached=None,
            entity_id_attached=None,
            is_completed=False,
            snoozed_until=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([reminder], include_private=True)
        assert summary == "Found 1 reminder."

    def test_generate_multiple_reminders(self, generator: SummaryGenerator):
        """Test generating summary with multiple reminders."""
        reminder1 = ReminderResult(
            id=1,
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Reminder 1",
            entity_type_attached=None,
            entity_id_attached=None,
            is_completed=False,
            snoozed_until=None,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        reminder2 = ReminderResult(
            id=2,
            reminder_time=datetime(2024, 1, 21, 14, 0, tzinfo=timezone.utc),
            message="Reminder 2",
            entity_type_attached=EntityType.PROJECT,
            entity_id_attached=1,
            is_completed=False,
            snoozed_until=None,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([reminder1, reminder2], include_private=True)
        assert summary == "Found 2 reminders."

    def test_generate_single_user(self, generator: SummaryGenerator):
        """Test generating summary with one user."""
        user = UserResult(
            id=1,
            full_name="Test User",
            email="test@example.com",
            timezone="America/New_York",
            week_boundary=WeekBoundary.SUNDAY_SATURDAY,
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([user], include_private=True)
        assert summary == "Found 1 user."

    def test_generate_multiple_users(self, generator: SummaryGenerator):
        """Test generating summary with multiple users."""
        user1 = UserResult(
            id=1,
            full_name="User 1",
            email="user1@example.com",
            timezone="America/New_York",
            week_boundary=WeekBoundary.SUNDAY_SATURDAY,
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        user2 = UserResult(
            id=2,
            full_name="User 2",
            email="user2@example.com",
            timezone="UTC",
            week_boundary=WeekBoundary.MONDAY_FRIDAY,
            created_at=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([user1, user2], include_private=True)
        assert summary == "Found 2 users."

    def test_generate_single_employment_history(self, generator: SummaryGenerator):
        """Test generating summary with one employment history."""
        from datetime import date

        eh = EmploymentHistoryResult(
            id=1,
            person_id=1,
            employer_id=1,
            start_date=date(2024, 1, 1),
            end_date=None,
            title="Software Engineer",
        )

        summary = generator.generate([eh], include_private=True)
        assert summary == "Found 1 employment history."

    def test_generate_multiple_employment_histories(self, generator: SummaryGenerator):
        """Test generating summary with employment histories."""
        from datetime import date

        eh1 = EmploymentHistoryResult(
            id=1,
            person_id=1,
            employer_id=1,
            start_date=date(2024, 1, 1),
            end_date=None,
            title="Software Engineer",
        )

        eh2 = EmploymentHistoryResult(
            id=2,
            person_id=1,
            employer_id=2,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            title="Junior Developer",
        )

        summary = generator.generate([eh1, eh2], include_private=True)
        assert summary == "Found 2 employment histories."

    def test_generate_three_entity_types(self, generator: SummaryGenerator):
        """Test generating summary with three or more entity types."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        meeting = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        project = ProjectResult(
            id=1,
            name="Project",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws, meeting, project], include_private=True)
        assert summary == "Found 1 work session (3.0 hours), 1 meeting, and 1 project."

    def test_generate_complex_mix_of_entities(self, generator: SummaryGenerator):
        """Test generating summary with complex mix of entity types."""
        ws1 = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work 1",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        ws2 = WorkSessionResult(
            id=2,
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 13, 30, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("4.5"),
            description="Work 2",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        meeting = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        project = ProjectResult(
            id=1,
            name="Project",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        person = PersonResult(
            id=1,
            full_name="John Doe",
            email=None,
            phone=None,
            company=None,
            title=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator.generate([ws1, ws2, meeting, project, person], include_private=True)
        assert summary == "Found 2 work sessions (7.5 hours), 1 meeting, 1 project, and 1 person."

    def test_generate_entities_without_privacy_level(self, generator: SummaryGenerator):
        """Test that entities without privacy_level are included regardless of privacy filtering."""
        project = ProjectResult(
            id=1,
            name="Project",
            client_id=1,
            status=ProjectStatus.ACTIVE,
            on_behalf_of=None,
            description=None,
            tags=[],
            created_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        person = PersonResult(
            id=1,
            full_name="John Doe",
            email=None,
            phone=None,
            company=None,
            title=None,
            notes=None,
            tags=[],
            created_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
        )

        # Both should be included even when exclude_private=False
        summary = generator.generate([project, person], include_private=False)
        assert summary == "Found 1 project and 1 person."

    def test_group_by_entity_type(self, generator: SummaryGenerator):
        """Test _group_by_entity_type method."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        meeting = MeetingResult(
            id=1,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting",
            attendees=[],
            project_id=None,
            description=None,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        )

        grouped = generator._group_by_entity_type([ws, meeting])

        assert "work_sessions" in grouped
        assert "meetings" in grouped
        assert len(grouped["work_sessions"]) == 1
        assert len(grouped["meetings"]) == 1
        assert grouped["work_sessions"][0].id == 1
        assert grouped["meetings"][0].id == 1

    def test_summarize_work_sessions(self, generator: SummaryGenerator):
        """Test _summarize_work_sessions method."""
        ws1 = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work 1",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        ws2 = WorkSessionResult(
            id=2,
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 13, 15, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("4.25"),
            description="Work 2",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator._summarize_work_sessions([ws1, ws2])
        assert summary == "2 work sessions (7.2 hours)"

    def test_summarize_single_work_session(self, generator: SummaryGenerator):
        """Test _summarize_work_sessions with single work session."""
        ws = WorkSessionResult(
            id=1,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=1,
            duration_hours=Decimal("3.0"),
            description="Work",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=[],
            created_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        )

        summary = generator._summarize_work_sessions([ws])
        assert summary == "1 work session (3.0 hours)"
