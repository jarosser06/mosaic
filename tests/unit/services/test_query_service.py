"""Unit tests for QueryService with privacy filtering."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.meeting import Meeting, MeetingAttendee
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        session.add(work_session)

        meeting = Meeting(
            title="Team Meeting",
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 10, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Early",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Middle",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws3 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 20),
            start_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
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
                start_time=datetime(2024, 1, i + 1, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, i + 1, 10, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Public",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws_internal = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Internal",
            privacy_level=PrivacyLevel.INTERNAL,
        )
        ws_private = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Public Meeting",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting_private = Meeting(
            title="Private Meeting",
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
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


class TestTextSearch:
    """Test full-text search functionality."""

    @pytest.mark.asyncio
    async def test_text_search_work_sessions(self, session: AsyncSession, project: Project):
        """Test text search on work session summaries."""
        ws1 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Implement feature X",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
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
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
            summary="Work on A",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=project2.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
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
    async def test_filter_meetings_by_person(self, session: AsyncSession, person: Person):
        """Test filtering meetings by person_id (attendee)."""
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        session.add(person2)
        await session.flush()

        meeting1 = Meeting(
            title="Meeting 1",
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Meeting 1",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting2 = Meeting(
            title="Meeting 2",
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
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


class TestEntitySpecificQueries:
    """Test entity-specific query methods."""

    @pytest.mark.asyncio
    async def test_query_notes_by_entity(self, session: AsyncSession, project: Project):
        """Test querying notes attached to specific entity."""
        from src.mosaic.models.note import Note

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
        from src.mosaic.models.note import Note

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
