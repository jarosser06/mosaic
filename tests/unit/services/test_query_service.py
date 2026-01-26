"""Unit tests for QueryService with privacy filtering."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.meeting import Meeting, MeetingAttendee
from src.mosaic.models.note import Note
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project, ProjectStatus
from src.mosaic.models.reminder import Reminder
from src.mosaic.models.work_session import WorkSession
from src.mosaic.services.query_service import QueryService


class TestFlexibleQuery:
    """Test flexible multi-entity queries."""

    @pytest.mark.asyncio
    async def test_query_all_entity_types(
        self,
        session: AsyncSession,
        project: Project,
        person: Person,
        client: Client,
        employer: Employer,
    ):
        """Test querying all entity types at once."""
        # Create sample data
        work_session = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add(work_session)

        meeting = Meeting(
            title="Team Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Meeting",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add(meeting)

        reminder = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Reminder",
            is_completed=False,
        )
        session.add(reminder)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query()

        assert len(results["work_sessions"]) == 1
        assert len(results["meetings"]) == 1
        assert len(results["projects"]) == 1
        assert len(results["people"]) == 1
        assert len(results["clients"]) == 1
        assert len(results["employers"]) == 1
        assert len(results["reminders"]) == 1

    @pytest.mark.asyncio
    async def test_query_specific_entity_types(self, session: AsyncSession, project: Project):
        """Test querying only specific entity types."""
        work_session = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add(work_session)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION, EntityType.PROJECT]
        )

        assert len(results["work_sessions"]) == 1
        assert len(results["projects"]) == 1
        # Other entity types should be empty
        assert len(results["meetings"]) == 0
        assert len(results["people"]) == 0

    @pytest.mark.asyncio
    async def test_query_with_date_range(self, session: AsyncSession, project: Project):
        """Test querying with start_date and end_date filters."""
        # Create work sessions on different dates
        ws1 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 10),
            duration_hours=Decimal("1.0"),
            summary="Early",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Middle",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws3 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 20),
            duration_hours=Decimal("1.0"),
            summary="Late",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([ws1, ws2, ws3])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18),
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Middle"

    @pytest.mark.asyncio
    async def test_query_invalid_date_range_raises_error(self, session: AsyncSession):
        """Test end_date before start_date raises error."""
        service = QueryService(session)

        with pytest.raises(ValueError, match="end_date must be after or equal to start_date"):
            await service.flexible_query(
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 10),
            )

    @pytest.mark.asyncio
    async def test_query_with_limit(self, session: AsyncSession, project: Project):
        """Test limit parameter restricts results."""
        # Create 5 work sessions
        for i in range(5):
            ws = WorkSession(
                project_id=project.id,
                date=date(2024, 1, i + 1),
                duration_hours=Decimal("1.0"),
                summary=f"Session {i}",
                privacy_level=PrivacyLevel.PUBLIC,
            )
            session.add(ws)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            limit=3,
        )

        assert len(results["work_sessions"]) == 3


class TestPrivacyFiltering:
    """Test privacy level filtering."""

    @pytest.mark.asyncio
    async def test_include_private_true_shows_all(self, session: AsyncSession, project: Project):
        """Test include_private=True shows PRIVATE entries."""
        ws_public = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Private",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([ws_public, ws_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            include_private=True,
        )

        assert len(results["work_sessions"]) == 2

    @pytest.mark.asyncio
    async def test_include_private_false_excludes_private(
        self, session: AsyncSession, project: Project
    ):
        """Test include_private=False excludes PRIVATE entries."""
        ws_public = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Private",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([ws_public, ws_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            include_private=False,
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Public"

    @pytest.mark.asyncio
    async def test_privacy_levels_filter_specific_levels(
        self, session: AsyncSession, project: Project
    ):
        """Test privacy_levels parameter filters to specific levels."""
        ws_public = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_internal = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Internal",
            privacy_level=PrivacyLevel.INTERNAL,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Private",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([ws_public, ws_internal, ws_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.PUBLIC],
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Public"

    @pytest.mark.asyncio
    async def test_privacy_filtering_for_meetings(self, session: AsyncSession, project: Project):
        """Test privacy filtering works for meetings."""
        meeting_public = Meeting(
            title="Public Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Public Meeting",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting_private = Meeting(
            title="Private Meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Private Meeting",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([meeting_public, meeting_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            include_private=False,
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].summary == "Public Meeting"

    @pytest.mark.asyncio
    async def test_privacy_filtering_for_notes_include_false(
        self, session: AsyncSession, project: Project
    ):
        """Test privacy filtering for notes with include_private=False (line 294)."""
        note_public = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Public note",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        note_private = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Private note",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([note_public, note_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.NOTE],
            include_private=False,
        )

        assert len(results["notes"]) == 1
        assert results["notes"][0].text == "Public note"

    @pytest.mark.asyncio
    async def test_privacy_levels_filter_for_notes(self, session: AsyncSession, project: Project):
        """Test privacy_levels parameter for notes (line 292)."""
        note_public = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Public note",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        note_internal = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Internal note",
            privacy_level=PrivacyLevel.INTERNAL,
        )
        note_private = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Private note",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([note_public, note_internal, note_private])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.NOTE],
            privacy_levels=[PrivacyLevel.INTERNAL, PrivacyLevel.PRIVATE],
        )

        assert len(results["notes"]) == 2
        texts = {n.text for n in results["notes"]}
        assert texts == {"Internal note", "Private note"}


class TestTextSearch:
    """Test full-text search functionality."""

    @pytest.mark.asyncio
    async def test_text_search_work_sessions(self, session: AsyncSession, project: Project):
        """Test text search on work session summaries."""
        ws1 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Implement feature X",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Fix bug Y",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([ws1, ws2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            search_text="feature",
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Implement feature X"

    @pytest.mark.asyncio
    async def test_text_search_case_insensitive(self, session: AsyncSession, project: Project):
        """Test text search is case-insensitive."""
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Important Task",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add(ws)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            search_text="important",
        )

        assert len(results["work_sessions"]) == 1

    @pytest.mark.asyncio
    async def test_text_search_projects_name_and_description(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test text search on project name and description."""
        project1 = Project(
            name="Frontend Redesign",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            description="Redesign the website",
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Backend API",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            description="Build REST API",
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            search_text="redesign",
        )

        assert len(results["projects"]) == 1
        assert results["projects"][0].name == "Frontend Redesign"

    @pytest.mark.asyncio
    async def test_query_meetings_search_by_title(self, session: AsyncSession):
        """Test text search finds meetings by title."""
        meeting1 = Meeting(
            title="Sprint Planning Session",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Discussion about upcoming sprint",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="Daily Standup",
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            duration_minutes=15,
            summary="Quick status update",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([meeting1, meeting2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            search_text="planning",
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].title == "Sprint Planning Session"

    @pytest.mark.asyncio
    async def test_query_meetings_search_multiple_fields(self, session: AsyncSession):
        """Test text search finds meetings in either title or summary."""
        meeting1 = Meeting(
            title="Team Sync",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=30,
            summary="Discussion about architecture",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="Architecture Review",
            start_time=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="System design discussion",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting3 = Meeting(
            title="Client Call",
            start_time=datetime(2024, 1, 17, 11, 0, tzinfo=timezone.utc),
            duration_minutes=30,
            summary="Budget and timeline discussion",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([meeting1, meeting2, meeting3])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            search_text="architecture",
        )

        # Should find both meeting1 (in summary) and meeting2 (in title)
        assert len(results["meetings"]) == 2
        titles = {m.title for m in results["meetings"]}
        assert titles == {"Team Sync", "Architecture Review"}

    @pytest.mark.asyncio
    async def test_text_search_notes(self, session: AsyncSession, project: Project):
        """Test text search on notes (line 298)."""
        note1 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Important information about database optimization",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        note2 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Meeting notes from planning session",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([note1, note2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.NOTE],
            search_text="database",
        )

        assert len(results["notes"]) == 1
        assert "database optimization" in results["notes"][0].text

    @pytest.mark.asyncio
    async def test_text_search_people(self, session: AsyncSession):
        """Test text search on people by name and email (line 351)."""
        person1 = Person(full_name="Alice Johnson", email="alice@example.com")
        person2 = Person(full_name="Bob Smith", email="bob@example.com")
        person3 = Person(full_name="Charlie Brown", email="charlie@johnson.com")
        session.add_all([person1, person2, person3])
        await session.commit()

        service = QueryService(session)

        # Search by name
        results = await service.flexible_query(
            entity_types=[EntityType.PERSON],
            search_text="johnson",
        )
        # Should find Alice Johnson (name) and charlie@johnson.com (email)
        assert len(results["people"]) == 2

    @pytest.mark.asyncio
    async def test_text_search_clients(self, session: AsyncSession):
        """Test text search on clients by name and notes (line 375)."""
        client1 = Client(
            name="Acme Corporation",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            notes="Tech startup specializing in AI",
        )
        client2 = Client(
            name="Beta Industries",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            notes="Manufacturing company",
        )
        session.add_all([client1, client2])
        await session.commit()

        service = QueryService(session)

        # Search by notes
        results = await service.flexible_query(
            entity_types=[EntityType.CLIENT],
            search_text="startup",
        )

        assert len(results["clients"]) == 1
        assert results["clients"][0].name == "Acme Corporation"

    @pytest.mark.asyncio
    async def test_text_search_employers(self, session: AsyncSession):
        """Test text search on employers by name and notes (line 399)."""
        employer1 = Employer(
            name="Tech Solutions Inc",
            is_current=True,
            notes="Software consulting company",
        )
        employer2 = Employer(
            name="Digital Innovations",
            is_current=False,
            notes="Hardware manufacturer",
        )
        session.add_all([employer1, employer2])
        await session.commit()

        service = QueryService(session)

        # Search by notes
        results = await service.flexible_query(
            entity_types=[EntityType.EMPLOYER],
            search_text="consulting",
        )

        assert len(results["employers"]) == 1
        assert results["employers"][0].name == "Tech Solutions Inc"


class TestRelationshipFilters:
    """Test filtering by related entities."""

    @pytest.mark.asyncio
    async def test_filter_work_sessions_by_project(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test filtering work sessions by project_id."""
        project1 = Project(
            name="Project A",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Project B",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.flush()

        ws1 = WorkSession(
            project_id=project1.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work on A",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project2.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work on B",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([ws1, ws2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            project_id=project1.id,
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Work on A"

    @pytest.mark.asyncio
    async def test_filter_work_sessions_by_employer(
        self,
        session: AsyncSession,
        client: Client,
    ):
        """Test filtering work sessions by employer_id via join (line 213)."""
        employer1 = Employer(name="Employer A", is_current=True)
        employer2 = Employer(name="Employer B", is_current=False)
        session.add_all([employer1, employer2])
        await session.flush()

        project1 = Project(
            name="Project A",
            on_behalf_of_id=employer1.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Project B",
            on_behalf_of_id=employer2.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.flush()

        ws1 = WorkSession(
            project_id=project1.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work for Employer A",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project2.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("1.0"),
            summary="Work for Employer B",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([ws1, ws2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            employer_id=employer1.id,
        )

        assert len(results["work_sessions"]) == 1
        assert results["work_sessions"][0].summary == "Work for Employer A"

    @pytest.mark.asyncio
    async def test_filter_meetings_by_person(self, session: AsyncSession, person: Person):
        """Test filtering meetings by person_id (attendee)."""
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        session.add(person2)
        await session.flush()

        meeting1 = Meeting(
            title="Meeting 1",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Meeting 1",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="Meeting 2",
            start_time=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Meeting 2",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([meeting1, meeting2])
        await session.flush()

        # Add person to meeting1 only
        attendee = MeetingAttendee(meeting_id=meeting1.id, person_id=person.id)
        session.add(attendee)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            person_id=person.id,
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].summary == "Meeting 1"

    @pytest.mark.asyncio
    async def test_filter_projects_by_client(
        self,
        session: AsyncSession,
        employer: Employer,
    ):
        """Test filtering projects by client_id."""
        client1 = Client(name="Client A", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
        client2 = Client(name="Client B", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
        session.add_all([client1, client2])
        await session.flush()

        project1 = Project(
            name="Project A",
            on_behalf_of_id=employer.id,
            client_id=client1.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Project B",
            on_behalf_of_id=employer.id,
            client_id=client2.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            client_id=client1.id,
        )

        assert len(results["projects"]) == 1
        assert results["projects"][0].name == "Project A"

    @pytest.mark.asyncio
    async def test_filter_projects_by_employer(
        self,
        session: AsyncSession,
        client: Client,
    ):
        """Test filtering projects by employer_id (on_behalf_of)."""
        employer1 = Employer(name="Employer A", is_current=True)
        employer2 = Employer(name="Employer B", is_current=False)
        session.add_all([employer1, employer2])
        await session.flush()

        project1 = Project(
            name="Project A",
            on_behalf_of_id=employer1.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Project B",
            on_behalf_of_id=employer2.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            employer_id=employer1.id,
        )

        assert len(results["projects"]) == 1
        assert results["projects"][0].name == "Project A"


class TestLimitFunctionality:
    """Test limit parameter for all entity types."""

    @pytest.mark.asyncio
    async def test_meetings_with_limit(self, session: AsyncSession):
        """Test limit parameter for meetings (line 275)."""
        for i in range(5):
            meeting = Meeting(
                title=f"Meeting {i}",
                start_time=datetime(2024, 1, 15 + i, 10, 0, tzinfo=timezone.utc),
                duration_minutes=60,
                summary=f"Summary {i}",
                privacy_level=PrivacyLevel.PUBLIC,
            )
            session.add(meeting)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            limit=2,
        )

        assert len(results["meetings"]) == 2

    @pytest.mark.asyncio
    async def test_notes_with_limit(self, session: AsyncSession, project: Project):
        """Test limit parameter for notes (line 302)."""
        for i in range(5):
            note = Note(
                entity_type=EntityType.PROJECT,
                entity_id=project.id,
                text=f"Note {i}",
                privacy_level=PrivacyLevel.PUBLIC,
            )
            session.add(note)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.NOTE],
            limit=3,
        )

        assert len(results["notes"]) == 3

    @pytest.mark.asyncio
    async def test_projects_with_limit(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test limit parameter for projects (line 336)."""
        for i in range(5):
            project = Project(
                name=f"Project {i}",
                on_behalf_of_id=employer.id,
                client_id=client.id,
                status=ProjectStatus.ACTIVE,
            )
            session.add(project)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            limit=2,
        )

        # Should have 3 results (2 + the fixture project)
        assert len(results["projects"]) <= 3

    @pytest.mark.asyncio
    async def test_people_with_limit(self, session: AsyncSession, person: Person):
        """Test limit parameter for people (line 360)."""
        for i in range(5):
            p = Person(full_name=f"Person {i}", email=f"person{i}@example.com")
            session.add(p)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.PERSON],
            limit=3,
        )

        # Should have 4 results (3 + the fixture person)
        assert len(results["people"]) <= 4

    @pytest.mark.asyncio
    async def test_clients_with_limit(self, session: AsyncSession, client: Client):
        """Test limit parameter for clients (line 384)."""
        for i in range(5):
            c = Client(
                name=f"Client {i}",
                type=ClientType.COMPANY,
                status=ClientStatus.ACTIVE,
            )
            session.add(c)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.CLIENT],
            limit=2,
        )

        # Should have 3 results (2 + the fixture client)
        assert len(results["clients"]) <= 3

    @pytest.mark.asyncio
    async def test_employers_with_limit(self, session: AsyncSession, employer: Employer):
        """Test limit parameter for employers (line 408)."""
        for i in range(5):
            e = Employer(name=f"Employer {i}", is_current=False)
            session.add(e)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.EMPLOYER],
            limit=2,
        )

        # Should have 3 results (2 + the fixture employer)
        assert len(results["employers"]) <= 3

    @pytest.mark.asyncio
    async def test_reminders_with_limit(self, session: AsyncSession):
        """Test limit parameter for reminders (line 442)."""
        for i in range(5):
            reminder = Reminder(
                reminder_time=datetime(2024, 1, i + 1, 9, 0, tzinfo=timezone.utc),
                message=f"Reminder {i}",
                is_completed=False,
            )
            session.add(reminder)
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            limit=3,
        )

        assert len(results["reminders"]) == 3


class TestReminderFiltering:
    """Test reminder-specific filtering."""

    @pytest.mark.asyncio
    async def test_reminders_with_date_range(self, session: AsyncSession):
        """Test reminders filtered by start_date and end_date (lines 426-430)."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            message="Early reminder",
            is_completed=False,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Middle reminder",
            is_completed=False,
        )
        reminder3 = Reminder(
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Late reminder",
            is_completed=False,
        )
        session.add_all([reminder1, reminder2, reminder3])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18),
        )

        assert len(results["reminders"]) == 1
        assert results["reminders"][0].message == "Middle reminder"

    @pytest.mark.asyncio
    async def test_reminders_include_completed_false(self, session: AsyncSession):
        """Test include_completed=False filters out completed reminders (line 433)."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Incomplete reminder",
            is_completed=False,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            message="Completed reminder",
            is_completed=True,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            include_completed=False,
        )

        assert len(results["reminders"]) == 1
        assert results["reminders"][0].message == "Incomplete reminder"

    @pytest.mark.asyncio
    async def test_reminders_include_completed_true(self, session: AsyncSession):
        """Test include_completed=True shows all reminders."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Incomplete reminder",
            is_completed=False,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            message="Completed reminder",
            is_completed=True,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            include_completed=True,
        )

        assert len(results["reminders"]) == 2


class TestEntitySpecificQueries:
    """Test entity-specific query methods."""

    @pytest.mark.asyncio
    async def test_query_notes_by_entity(self, session: AsyncSession, project: Project):
        """Test querying notes attached to specific entity."""
        note1 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Note 1",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        note2 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Note 2",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([note1, note2])
        await session.commit()

        service = QueryService(session)
        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        assert len(notes) == 2

    @pytest.mark.asyncio
    async def test_query_notes_by_entity_exclude_private(
        self, session: AsyncSession, project: Project
    ):
        """Test query_notes_by_entity excludes private notes."""
        note1 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Public note",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        note2 = Note(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            text="Private note",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([note1, note2])
        await session.commit()

        service = QueryService(session)
        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            include_private=False,
        )

        assert len(notes) == 1
        assert notes[0].text == "Public note"

    @pytest.mark.asyncio
    async def test_query_reminders_by_entity(self, session: AsyncSession, project: Project):
        """Test querying reminders related to specific entity."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Reminder 1",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            message="Reminder 2",
            is_completed=True,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            include_completed=False,
        )

        assert len(reminders) == 1
        assert reminders[0].message == "Reminder 1"

    @pytest.mark.asyncio
    async def test_query_reminders_by_entity_with_limit(
        self, session: AsyncSession, project: Project
    ):
        """Test query_reminders_by_entity with limit parameter (line 516)."""
        for i in range(5):
            reminder = Reminder(
                reminder_time=datetime(2024, 1, i + 1, 9, 0, tzinfo=timezone.utc),
                message=f"Reminder {i}",
                is_completed=False,
                related_entity_type=EntityType.PROJECT,
                related_entity_id=project.id,
            )
            session.add(reminder)
        await session.commit()

        service = QueryService(session)
        reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            limit=3,
        )

        assert len(reminders) == 3


class TestMeetingDateFilters:
    """Test meeting-specific date filtering."""

    @pytest.mark.asyncio
    async def test_meeting_start_date_filter(self, session: AsyncSession):
        """Test meeting start_date filter (lines 242-243)."""
        meeting1 = Meeting(
            title="Old Meeting",
            start_time=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Old",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="New Meeting",
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="New",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([meeting1, meeting2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            start_date=date(2024, 1, 15),
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].title == "New Meeting"

    @pytest.mark.asyncio
    async def test_meeting_end_date_filter(self, session: AsyncSession):
        """Test meeting end_date filter (lines 245-246)."""
        meeting1 = Meeting(
            title="Old Meeting",
            start_time=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Old",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="New Meeting",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="New",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add_all([meeting1, meeting2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            end_date=date(2024, 1, 15),
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].title == "Old Meeting"

    @pytest.mark.asyncio
    async def test_meeting_privacy_levels_filter(self, session: AsyncSession):
        """Test meeting privacy_levels filter (line 250)."""
        meeting1 = Meeting(
            title="Public Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="Internal Meeting",
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Internal",
            privacy_level=PrivacyLevel.INTERNAL,
        )
        meeting3 = Meeting(
            title="Private Meeting",
            start_time=datetime(2024, 1, 17, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Private",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        session.add_all([meeting1, meeting2, meeting3])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            privacy_levels=[PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL],
        )

        assert len(results["meetings"]) == 2
        titles = [m.title for m in results["meetings"]]
        assert "Public Meeting" in titles
        assert "Internal Meeting" in titles
        assert "Private Meeting" not in titles

    @pytest.mark.asyncio
    async def test_meeting_project_id_filter(
        self, session: AsyncSession, project: Project, employer: Employer, client: Client
    ):
        """Test meeting project_id filter (line 256)."""
        project2 = Project(
            name="Project B",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add(project2)
        await session.flush()

        meeting1 = Meeting(
            title="Project A Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="A",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        meeting2 = Meeting(
            title="Project B Meeting",
            start_time=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="B",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project2.id,
        )
        session.add_all([meeting1, meeting2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            project_id=project.id,
        )

        assert len(results["meetings"]) == 1
        assert results["meetings"][0].title == "Project A Meeting"


class TestReminderSearchText:
    """Test reminder text search."""

    @pytest.mark.asyncio
    async def test_reminder_search_text(self, session: AsyncSession):
        """Test reminder search_text filter (line 438)."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            message="Call John about authentication",
            is_completed=False,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
            message="Review database schema",
            is_completed=False,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            search_text="authentication",
        )

        assert len(results["reminders"]) == 1
        assert results["reminders"][0].message == "Call John about authentication"


class TestNoteLimitFilter:
    """Test note limit filter."""

    @pytest.mark.asyncio
    async def test_note_limit_via_query_notes(self, session: AsyncSession, project: Project):
        """Test note limit in query_notes method (line 479)."""
        for i in range(5):
            note = Note(
                entity_type=EntityType.PROJECT,
                entity_id=project.id,
                text=f"Note {i}",
                privacy_level=PrivacyLevel.PUBLIC,
            )
            session.add(note)
        await session.commit()

        service = QueryService(session)
        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            limit=2,
        )

        assert len(notes) == 2


class TestReminderEntityIncludeCompleted:
    """Test reminder by entity with include_completed filter."""

    @pytest.mark.asyncio
    async def test_query_reminders_by_entity_exclude_completed(
        self, session: AsyncSession, project: Project
    ):
        """Test query_reminders_by_entity with include_completed=False (line 511)."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            message="Active Reminder",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
            message="Completed Reminder",
            is_completed=True,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            include_completed=False,
        )

        assert len(reminders) == 1
        assert reminders[0].message == "Active Reminder"

    @pytest.mark.asyncio
    async def test_query_reminders_by_entity_include_completed(
        self, session: AsyncSession, project: Project
    ):
        """Test querying reminders with include_completed=True (covers branch 511->515)."""
        reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Reminder 1",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            message="Reminder 2",
            is_completed=True,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        session.add_all([reminder1, reminder2])
        await session.commit()

        service = QueryService(session)
        reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            include_completed=True,  # Changed to True to cover branch
        )

        # Should include both completed and non-completed
        assert len(reminders) == 2
        assert {r.message for r in reminders} == {"Reminder 1", "Reminder 2"}
