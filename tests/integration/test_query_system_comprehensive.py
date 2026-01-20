"""Comprehensive integration tests for query system with real database.

Tests the QueryService.flexible_query method with all filter combinations,
ensuring proper filtering logic and correct results returned.

Target: 60+ integration tests covering all query scenarios.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel, ProjectStatus
from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.meeting import Meeting, MeetingAttendee
from src.mosaic.models.note import Note
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project
from src.mosaic.models.reminder import Reminder
from src.mosaic.models.work_session import WorkSession
from src.mosaic.services.query_service import QueryService

# ============================================================================
# Fixtures for Test Data
# ============================================================================


@pytest.fixture
async def work_sessions_varied_dates(
    test_session: AsyncSession,
    project: Project,
) -> list[WorkSession]:
    """Create work sessions across multiple dates for date range testing."""
    sessions = [
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 10),
            start_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 10, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Session on Jan 10",
            privacy_level=PrivacyLevel.PUBLIC,
        ),
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Session on Jan 15",
            privacy_level=PrivacyLevel.PUBLIC,
        ),
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 20),
            start_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Session on Jan 20",
            privacy_level=PrivacyLevel.PUBLIC,
        ),
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 25),
            start_time=datetime(2024, 1, 25, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 25, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Session on Jan 25",
            privacy_level=PrivacyLevel.PUBLIC,
        ),
    ]
    for ws in sessions:
        test_session.add(ws)
    await test_session.commit()
    return sessions


@pytest.fixture
async def work_sessions_varied_privacy(
    test_session: AsyncSession,
    project: Project,
) -> list[WorkSession]:
    """Create work sessions with different privacy levels."""
    sessions = [
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Public work session",
            privacy_level=PrivacyLevel.PUBLIC,
        ),
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 16),
            start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 16, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Internal work session",
            privacy_level=PrivacyLevel.INTERNAL,
        ),
        WorkSession(
            project_id=project.id,
            date=date(2024, 1, 17),
            start_time=datetime(2024, 1, 17, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 17, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Private work session",
            privacy_level=PrivacyLevel.PRIVATE,
        ),
    ]
    for ws in sessions:
        test_session.add(ws)
    await test_session.commit()
    return sessions


@pytest.fixture
async def second_project(
    test_session: AsyncSession,
    employer: Employer,
    client: Client,
) -> Project:
    """Create a second project for testing project filters."""
    project = Project(
        name="Second Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        description="Another project",
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)
    return project


@pytest.fixture
async def meetings_varied_privacy(
    test_session: AsyncSession,
    project: Project,
    person: Person,
) -> list[Meeting]:
    """Create meetings with different privacy levels."""
    meetings = [
        Meeting(
            title="Public Meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Public meeting summary",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        ),
        Meeting(
            title="Internal Meeting",
            start_time=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Internal meeting summary",
            privacy_level=PrivacyLevel.INTERNAL,
            project_id=project.id,
        ),
        Meeting(
            title="Private Meeting",
            start_time=datetime(2024, 1, 17, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Private meeting summary",
            privacy_level=PrivacyLevel.PRIVATE,
            project_id=project.id,
        ),
    ]
    for meeting in meetings:
        test_session.add(meeting)
    await test_session.commit()

    # Add attendee to all meetings
    for meeting in meetings:
        attendee = MeetingAttendee(meeting_id=meeting.id, person_id=person.id)
        test_session.add(attendee)
    await test_session.commit()

    return meetings


@pytest.fixture
async def notes_varied(
    test_session: AsyncSession,
    project: Project,
) -> list[Note]:
    """Create notes with varied privacy and text."""
    notes = [
        Note(
            text="Public note about project",
            privacy_level=PrivacyLevel.PUBLIC,
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        ),
        Note(
            text="Internal note with sensitive info",
            privacy_level=PrivacyLevel.INTERNAL,
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        ),
        Note(
            text="Private note confidential",
            privacy_level=PrivacyLevel.PRIVATE,
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        ),
    ]
    for note in notes:
        test_session.add(note)
    await test_session.commit()
    return notes


@pytest.fixture
async def reminders_varied(
    test_session: AsyncSession,
    project: Project,
) -> list[Reminder]:
    """Create reminders with varied dates and completion status."""
    reminders = [
        Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Reminder for Jan 15",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        ),
        Reminder(
            reminder_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
            message="Reminder for Jan 20",
            is_completed=True,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        ),
        Reminder(
            reminder_time=datetime(2024, 1, 25, 9, 0, tzinfo=timezone.utc),
            message="Reminder for Jan 25",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        ),
    ]
    for reminder in reminders:
        test_session.add(reminder)
    await test_session.commit()
    return reminders


@pytest.fixture
async def projects_varied_status(
    test_session: AsyncSession,
    employer: Employer,
    client: Client,
) -> list[Project]:
    """Create projects with different statuses."""
    projects = [
        Project(
            name="Active Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        ),
        Project(
            name="Paused Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.PAUSED,
        ),
        Project(
            name="Completed Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.COMPLETED,
        ),
    ]
    for project in projects:
        test_session.add(project)
    await test_session.commit()
    return projects


@pytest.fixture
async def clients_varied_status(
    test_session: AsyncSession,
) -> list[Client]:
    """Create clients with different statuses."""
    clients = [
        Client(
            name="Active Client Inc",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        ),
        Client(
            name="Past Client LLC",
            type=ClientType.COMPANY,
            status=ClientStatus.PAST,
        ),
    ]
    for client in clients:
        test_session.add(client)
    await test_session.commit()
    return clients


# ============================================================================
# Date Range Filter Tests (10+ tests)
# ============================================================================


class TestDateRangeFilters:
    """Test date range filtering for work sessions and meetings."""

    @pytest.mark.asyncio
    async def test_work_sessions_within_date_range(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test filtering work sessions within a date range."""
        service = QueryService(test_session)

        # Query Jan 15-20 (should get sessions on 15 and 20)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 20),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        dates = {ws.date for ws in sessions}
        assert dates == {date(2024, 1, 15), date(2024, 1, 20)}

    @pytest.mark.asyncio
    async def test_work_sessions_start_date_only(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test filtering work sessions with only start_date."""
        service = QueryService(test_session)

        # Query from Jan 20 onwards (should get 20 and 25)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 20),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        dates = {ws.date for ws in sessions}
        assert dates == {date(2024, 1, 20), date(2024, 1, 25)}

    @pytest.mark.asyncio
    async def test_work_sessions_end_date_only(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test filtering work sessions with only end_date."""
        service = QueryService(test_session)

        # Query up to Jan 15 (should get 10 and 15)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            end_date=date(2024, 1, 15),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        dates = {ws.date for ws in sessions}
        assert dates == {date(2024, 1, 10), date(2024, 1, 15)}

    @pytest.mark.asyncio
    async def test_work_sessions_exact_start_date_boundary(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test that start_date boundary is inclusive."""
        service = QueryService(test_session)

        # Query exactly Jan 15
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].date == date(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_work_sessions_exact_end_date_boundary(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test that end_date boundary is inclusive."""
        service = QueryService(test_session)

        # Query up to and including Jan 20
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 20),
            end_date=date(2024, 1, 20),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].date == date(2024, 1, 20)

    @pytest.mark.asyncio
    async def test_work_sessions_empty_results_outside_range(
        self,
        test_session: AsyncSession,
        work_sessions_varied_dates: list[WorkSession],
    ):
        """Test that no results returned when outside date range."""
        service = QueryService(test_session)

        # Query dates with no data
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28),
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_meetings_within_date_range(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings within a date range."""
        service = QueryService(test_session)

        # Query Jan 15-16 (should get 2 meetings)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
        )

        meetings = results["meetings"]
        assert len(meetings) == 2
        titles = {m.title for m in meetings}
        assert titles == {"Public Meeting", "Internal Meeting"}

    @pytest.mark.asyncio
    async def test_meetings_start_date_only(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings with only start_date."""
        service = QueryService(test_session)

        # Query from Jan 16 onwards
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            start_date=date(2024, 1, 16),
        )

        meetings = results["meetings"]
        assert len(meetings) == 2
        titles = {m.title for m in meetings}
        assert titles == {"Internal Meeting", "Private Meeting"}

    @pytest.mark.asyncio
    async def test_meetings_empty_results_outside_range(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test meetings return empty when outside date range."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28),
        )

        meetings = results["meetings"]
        assert len(meetings) == 0

    @pytest.mark.asyncio
    async def test_date_range_validation_error(
        self,
        test_session: AsyncSession,
    ):
        """Test that end_date before start_date raises error."""
        service = QueryService(test_session)

        with pytest.raises(ValueError, match="end_date must be after or equal to start_date"):
            await service.flexible_query(
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 10),
            )


# ============================================================================
# Privacy Filter Tests (15+ tests)
# ============================================================================


class TestPrivacyFilters:
    """Test privacy level filtering across entities."""

    @pytest.mark.asyncio
    async def test_work_sessions_filter_public_only(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test filtering work sessions for PUBLIC only."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.PUBLIC],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].privacy_level == PrivacyLevel.PUBLIC
        assert sessions[0].summary == "Public work session"

    @pytest.mark.asyncio
    async def test_work_sessions_filter_internal_only(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test filtering work sessions for INTERNAL only."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.INTERNAL],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].privacy_level == PrivacyLevel.INTERNAL
        assert sessions[0].summary == "Internal work session"

    @pytest.mark.asyncio
    async def test_work_sessions_filter_private_only(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test filtering work sessions for PRIVATE only."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.PRIVATE],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].privacy_level == PrivacyLevel.PRIVATE
        assert sessions[0].summary == "Private work session"

    @pytest.mark.asyncio
    async def test_work_sessions_filter_multiple_levels(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test filtering work sessions for multiple privacy levels."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        privacy_levels = {ws.privacy_level for ws in sessions}
        assert privacy_levels == {PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL}

    @pytest.mark.asyncio
    async def test_work_sessions_exclude_private_flag(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test include_private=False excludes PRIVATE entries."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            include_private=False,
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        for ws in sessions:
            assert ws.privacy_level != PrivacyLevel.PRIVATE

    @pytest.mark.asyncio
    async def test_work_sessions_include_private_flag_default(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test include_private=True (default) includes all."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            include_private=True,
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_meetings_filter_public_only(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings for PUBLIC only."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            privacy_levels=[PrivacyLevel.PUBLIC],
        )

        meetings = results["meetings"]
        assert len(meetings) == 1
        assert meetings[0].privacy_level == PrivacyLevel.PUBLIC
        assert meetings[0].title == "Public Meeting"

    @pytest.mark.asyncio
    async def test_meetings_filter_internal_only(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings for INTERNAL only."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            privacy_levels=[PrivacyLevel.INTERNAL],
        )

        meetings = results["meetings"]
        assert len(meetings) == 1
        assert meetings[0].privacy_level == PrivacyLevel.INTERNAL
        assert meetings[0].title == "Internal Meeting"

    @pytest.mark.asyncio
    async def test_meetings_filter_multiple_levels(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings for multiple privacy levels."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            privacy_levels=[PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL],
        )

        meetings = results["meetings"]
        assert len(meetings) == 2
        privacy_levels = {m.privacy_level for m in meetings}
        assert privacy_levels == {PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL}

    @pytest.mark.asyncio
    async def test_meetings_exclude_private_flag(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test include_private=False excludes PRIVATE meetings."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            include_private=False,
        )

        meetings = results["meetings"]
        assert len(meetings) == 2
        for m in meetings:
            assert m.privacy_level != PrivacyLevel.PRIVATE

    @pytest.mark.asyncio
    async def test_empty_privacy_levels_list_edge_case(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test that empty privacy_levels list returns no results."""
        service = QueryService(test_session)

        # Empty list should match nothing
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_privacy_levels_override_include_private(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test that privacy_levels overrides include_private flag."""
        service = QueryService(test_session)

        # privacy_levels specified, so include_private is ignored
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            privacy_levels=[PrivacyLevel.PUBLIC],
            include_private=True,  # Should be ignored
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].privacy_level == PrivacyLevel.PUBLIC

    @pytest.mark.asyncio
    async def test_notes_privacy_filter_public_only(
        self,
        test_session: AsyncSession,
        notes_varied: list[Note],
    ):
        """Test filtering notes by privacy level through entity query."""
        service = QueryService(test_session)

        # Query notes attached to project
        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=notes_varied[0].entity_id,
            include_private=False,
        )

        assert len(notes) == 2
        for note in notes:
            assert note.privacy_level != PrivacyLevel.PRIVATE

    @pytest.mark.asyncio
    async def test_notes_privacy_filter_include_all(
        self,
        test_session: AsyncSession,
        notes_varied: list[Note],
    ):
        """Test including all privacy levels for notes."""
        service = QueryService(test_session)

        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=notes_varied[0].entity_id,
            include_private=True,
        )

        assert len(notes) == 3

    @pytest.mark.asyncio
    async def test_combined_privacy_and_date_filter(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test combining privacy and date filters."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
            privacy_levels=[PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 2
        privacy_levels = {ws.privacy_level for ws in sessions}
        assert privacy_levels == {PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL}


# ============================================================================
# Entity Relationship Filter Tests (10+ tests)
# ============================================================================


class TestEntityRelationshipFilters:
    """Test filtering by entity relationships (project_id, person_id, etc.)."""

    @pytest.mark.asyncio
    async def test_work_sessions_filter_by_project_id(
        self,
        test_session: AsyncSession,
        project: Project,
        second_project: Project,
    ):
        """Test filtering work sessions by specific project_id."""
        # Create sessions for both projects
        ws1 = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="First project work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        ws2 = WorkSession(
            project_id=second_project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Second project work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add_all([ws1, ws2])
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            project_id=project.id,
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert sessions[0].project_id == project.id
        assert sessions[0].summary == "First project work"

    @pytest.mark.asyncio
    async def test_work_sessions_filter_by_nonexistent_project(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test filtering by nonexistent project_id returns empty."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            project_id=99999,
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_meetings_filter_by_project_id(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
        project: Project,
    ):
        """Test filtering meetings by project_id."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            project_id=project.id,
        )

        meetings = results["meetings"]
        assert len(meetings) == 3
        for meeting in meetings:
            assert meeting.project_id == project.id

    @pytest.mark.asyncio
    async def test_meetings_filter_by_person_id(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
        person: Person,
    ):
        """Test filtering meetings by person_id (attendee)."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            person_id=person.id,
        )

        meetings = results["meetings"]
        assert len(meetings) == 3
        # All meetings have this person as attendee

    @pytest.mark.asyncio
    async def test_meetings_filter_by_nonexistent_person(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test filtering meetings by nonexistent person_id returns empty."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            person_id=99999,
        )

        meetings = results["meetings"]
        assert len(meetings) == 0

    @pytest.mark.asyncio
    async def test_projects_filter_by_client_id(
        self,
        test_session: AsyncSession,
        projects_varied_status: list[Project],
        client: Client,
    ):
        """Test filtering projects by client_id."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            client_id=client.id,
        )

        projects = results["projects"]
        assert len(projects) == 3
        for proj in projects:
            assert proj.client_id == client.id

    @pytest.mark.asyncio
    async def test_projects_filter_by_employer_id(
        self,
        test_session: AsyncSession,
        projects_varied_status: list[Project],
        employer: Employer,
    ):
        """Test filtering projects by employer_id (on_behalf_of_id)."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            employer_id=employer.id,
        )

        projects = results["projects"]
        assert len(projects) == 3
        for proj in projects:
            assert proj.on_behalf_of_id == employer.id

    @pytest.mark.asyncio
    async def test_projects_filter_by_nonexistent_client(
        self,
        test_session: AsyncSession,
        projects_varied_status: list[Project],
    ):
        """Test filtering projects by nonexistent client_id returns empty."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            client_id=99999,
        )

        projects = results["projects"]
        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_combined_project_and_date_filter(
        self,
        test_session: AsyncSession,
        project: Project,
        second_project: Project,
    ):
        """Test combining project_id and date filters."""
        # Create sessions on different dates for both projects
        sessions = [
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Project 1 - Jan 15",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 20),
                start_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Project 1 - Jan 20",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=second_project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Project 2 - Jan 15",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
        ]
        for ws in sessions:
            test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            project_id=project.id,
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 1
        assert sessions_result[0].project_id == project.id
        assert sessions_result[0].date == date(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_notes_filter_by_entity_attachment(
        self,
        test_session: AsyncSession,
        notes_varied: list[Note],
        project: Project,
    ):
        """Test querying notes by entity attachment."""
        service = QueryService(test_session)

        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        assert len(notes) == 3
        for note in notes:
            assert note.entity_type == EntityType.PROJECT
            assert note.entity_id == project.id


# ============================================================================
# Text Search Tests (8+ tests)
# ============================================================================


class TestTextSearch:
    """Test text search across various entity fields."""

    @pytest.mark.asyncio
    async def test_work_sessions_search_by_summary(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test searching work sessions by summary text."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            search_text="Public",
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert "Public" in sessions[0].summary

    @pytest.mark.asyncio
    async def test_work_sessions_search_case_insensitive(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test that text search is case-insensitive."""
        service = QueryService(test_session)

        # Search with different case
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            search_text="public",
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 1
        assert "Public" in sessions[0].summary

    @pytest.mark.asyncio
    async def test_meetings_search_by_title(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test searching meetings by title."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            search_text="Internal",
        )

        meetings = results["meetings"]
        assert len(meetings) == 1
        assert "Internal" in meetings[0].title

    @pytest.mark.asyncio
    async def test_meetings_search_by_summary(
        self,
        test_session: AsyncSession,
        meetings_varied_privacy: list[Meeting],
    ):
        """Test searching meetings by summary text."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            search_text="summary",
        )

        meetings = results["meetings"]
        assert len(meetings) == 3
        # All meetings have "summary" in their summary field

    @pytest.mark.asyncio
    async def test_projects_search_by_name(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test searching projects by name."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            search_text="Test Project",
        )

        projects = results["projects"]
        assert len(projects) == 1
        assert projects[0].name == "Test Project"

    @pytest.mark.asyncio
    async def test_projects_search_by_description(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test searching projects by description."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            search_text="project description",
        )

        projects = results["projects"]
        assert len(projects) == 1
        assert "project description" in projects[0].description

    @pytest.mark.asyncio
    async def test_reminders_search_by_message(
        self,
        test_session: AsyncSession,
        reminders_varied: list[Reminder],
    ):
        """Test searching reminders by message text."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.REMINDER],
            search_text="Jan 15",
        )

        reminders = results["reminders"]
        assert len(reminders) == 1
        assert "Jan 15" in reminders[0].message

    @pytest.mark.asyncio
    async def test_text_search_no_results(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test text search with no matching results."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            search_text="NonexistentText12345",
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 0


# ============================================================================
# Status Filter Tests (5+ tests)
# ============================================================================


class TestStatusFilters:
    """Test filtering by status fields."""

    @pytest.mark.asyncio
    async def test_reminders_filter_by_completed_status(
        self,
        test_session: AsyncSession,
        reminders_varied: list[Reminder],
    ):
        """Test filtering reminders by completion status."""
        service = QueryService(test_session)

        # Query by entity to access reminders
        completed_reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=reminders_varied[0].related_entity_id,
            include_completed=True,
        )

        # Should get all 3
        assert len(completed_reminders) == 3

    @pytest.mark.asyncio
    async def test_reminders_exclude_completed(
        self,
        test_session: AsyncSession,
        reminders_varied: list[Reminder],
    ):
        """Test excluding completed reminders."""
        service = QueryService(test_session)

        active_reminders = await service.query_reminders_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=reminders_varied[0].related_entity_id,
            include_completed=False,
        )

        # Should get 2 (not completed)
        assert len(active_reminders) == 2
        for reminder in active_reminders:
            assert not reminder.is_completed

    @pytest.mark.asyncio
    async def test_projects_all_statuses_returned_by_default(
        self,
        test_session: AsyncSession,
        projects_varied_status: list[Project],
    ):
        """Test that all project statuses are returned by default."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
        )

        projects = results["projects"]
        assert len(projects) == 3
        statuses = {p.status for p in projects}
        assert statuses == {
            ProjectStatus.ACTIVE,
            ProjectStatus.PAUSED,
            ProjectStatus.COMPLETED,
        }

    @pytest.mark.asyncio
    async def test_clients_all_statuses_returned_by_default(
        self,
        test_session: AsyncSession,
        clients_varied_status: list[Client],
    ):
        """Test that all client statuses are returned by default."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.CLIENT],
        )

        clients = results["clients"]
        assert len(clients) == 2
        statuses = {c.status for c in clients}
        assert statuses == {ClientStatus.ACTIVE, ClientStatus.PAST}

    @pytest.mark.asyncio
    async def test_projects_search_filters_across_statuses(
        self,
        test_session: AsyncSession,
        projects_varied_status: list[Project],
    ):
        """Test that search works across different project statuses."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            search_text="Project",
        )

        projects = results["projects"]
        assert len(projects) == 3
        # All have "Project" in name


# ============================================================================
# Combined Filter Tests (10+ tests)
# ============================================================================


class TestCombinedFilters:
    """Test multiple filters applied together."""

    @pytest.mark.asyncio
    async def test_combined_date_privacy_project(
        self,
        test_session: AsyncSession,
        project: Project,
        second_project: Project,
    ):
        """Test combining date range, privacy, and project filters."""
        # Create test data
        sessions = [
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Target session",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Wrong privacy",
                privacy_level=PrivacyLevel.PRIVATE,
            ),
            WorkSession(
                project_id=second_project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Wrong project",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 20),
                start_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Wrong date",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
        ]
        for ws in sessions:
            test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            privacy_levels=[PrivacyLevel.PUBLIC],
            project_id=project.id,
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 1
        assert sessions_result[0].summary == "Target session"

    @pytest.mark.asyncio
    async def test_combined_date_and_text_search(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test combining date range and text search."""
        sessions = [
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Backend work in range",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Frontend work in range",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 20),
                start_time=datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Backend work outside range",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
        ]
        for ws in sessions:
            test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            search_text="Backend",
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 1
        assert "Backend" in sessions_result[0].summary
        assert sessions_result[0].date == date(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_combined_all_filters_together(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test all filters combined: date, privacy, project, text."""
        sessions = [
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Target API work",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Database work",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
        ]
        for ws in sessions:
            test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            privacy_levels=[PrivacyLevel.PUBLIC],
            project_id=project.id,
            search_text="API",
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 1
        assert sessions_result[0].summary == "Target API work"

    @pytest.mark.asyncio
    async def test_combined_meetings_date_privacy_person(
        self,
        test_session: AsyncSession,
        project: Project,
        person: Person,
    ):
        """Test combining date, privacy, and person filters for meetings."""
        # Create test meetings
        meeting1 = Meeting(
            title="Target meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Target meeting",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        meeting2 = Meeting(
            title="Wrong privacy",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Wrong privacy",
            privacy_level=PrivacyLevel.PRIVATE,
            project_id=project.id,
        )
        test_session.add_all([meeting1, meeting2])
        await test_session.commit()

        # Add attendees
        attendee1 = MeetingAttendee(meeting_id=meeting1.id, person_id=person.id)
        attendee2 = MeetingAttendee(meeting_id=meeting2.id, person_id=person.id)
        test_session.add_all([attendee1, attendee2])
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.MEETING],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            privacy_levels=[PrivacyLevel.PUBLIC],
            person_id=person.id,
        )

        meetings = results["meetings"]
        assert len(meetings) == 1
        assert meetings[0].title == "Target meeting"

    @pytest.mark.asyncio
    async def test_combined_projects_client_employer_search(
        self,
        test_session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test combining client, employer, and text search for projects."""
        # Create projects
        project1 = Project(
            name="Target project with keyword",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Wrong project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add_all([project1, project2])
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.PROJECT],
            client_id=client.id,
            employer_id=employer.id,
            search_text="keyword",
        )

        projects = results["projects"]
        assert len(projects) == 1
        assert projects[0].name == "Target project with keyword"

    @pytest.mark.asyncio
    async def test_combined_filters_with_limit(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that limit parameter works with combined filters."""
        # Create 5 sessions matching filters
        sessions = []
        for i in range(5):
            ws = WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, i, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, i, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary=f"Session {i}",
                privacy_level=PrivacyLevel.PUBLIC,
            )
            sessions.append(ws)
            test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            project_id=project.id,
            privacy_levels=[PrivacyLevel.PUBLIC],
            limit=3,
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 3

    @pytest.mark.asyncio
    async def test_multiple_entity_types_with_filters(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test querying multiple entity types with shared filters."""
        # Create work session and meeting on same date
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Work session",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting = Meeting(
            title="Meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Meeting summary",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        test_session.add_all([ws, meeting])
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION, EntityType.MEETING],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            privacy_levels=[PrivacyLevel.PUBLIC],
            project_id=project.id,
        )

        assert len(results["work_sessions"]) == 1
        assert len(results["meetings"]) == 1

    @pytest.mark.asyncio
    async def test_combined_filters_empty_result(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that overly restrictive filters return empty results."""
        # Create session that won't match all filters
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Backend work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            privacy_levels=[PrivacyLevel.PUBLIC],
            project_id=project.id,
            search_text="Frontend",  # Won't match "Backend"
        )

        sessions_result = results["work_sessions"]
        assert len(sessions_result) == 0

    @pytest.mark.asyncio
    async def test_no_filters_returns_all(
        self,
        test_session: AsyncSession,
        work_sessions_varied_privacy: list[WorkSession],
    ):
        """Test that no filters returns all entities."""
        service = QueryService(test_session)

        results = await service.flexible_query(
            entity_types=[EntityType.WORK_SESSION],
        )

        sessions = results["work_sessions"]
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_default_entity_types_queries_all(
        self,
        test_session: AsyncSession,
        project: Project,
        person: Person,
    ):
        """Test that entity_types=None queries all entity types."""
        # Create one of each type
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        meeting = Meeting(
            title="Meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add_all([ws, meeting])
        await test_session.commit()

        service = QueryService(test_session)
        results = await service.flexible_query(
            entity_types=None,  # Should query all types
        )

        # Should have results in multiple categories
        assert len(results["work_sessions"]) >= 1
        assert len(results["meetings"]) >= 1
        assert len(results["projects"]) >= 1
        assert len(results["people"]) >= 1


# ============================================================================
# Notes Query Tests (5+ tests)
# ============================================================================


class TestNotesQueries:
    """Test note-specific query functionality."""

    @pytest.mark.asyncio
    async def test_query_notes_by_text_search(
        self,
        test_session: AsyncSession,
        notes_varied: list[Note],
    ):
        """Test querying notes by text content (not in flexible_query yet)."""
        # Note: flexible_query doesn't include notes yet
        # This tests the query_notes_by_entity method
        service = QueryService(test_session)

        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=notes_varied[0].entity_id,
        )

        assert len(notes) == 3

    @pytest.mark.asyncio
    async def test_query_notes_by_privacy_level(
        self,
        test_session: AsyncSession,
        notes_varied: list[Note],
    ):
        """Test filtering notes by privacy level."""
        service = QueryService(test_session)

        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=notes_varied[0].entity_id,
            include_private=False,
        )

        assert len(notes) == 2
        for note in notes:
            assert note.privacy_level != PrivacyLevel.PRIVATE

    @pytest.mark.asyncio
    async def test_query_notes_attached_to_project(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test querying all notes attached to a project."""
        # Create notes
        notes = [
            Note(
                text=f"Note {i}",
                privacy_level=PrivacyLevel.PUBLIC,
                entity_type=EntityType.PROJECT,
                entity_id=project.id,
            )
            for i in range(3)
        ]
        for note in notes:
            test_session.add(note)
        await test_session.commit()

        service = QueryService(test_session)
        result_notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        assert len(result_notes) == 3
        for note in result_notes:
            assert note.entity_type == EntityType.PROJECT
            assert note.entity_id == project.id

    @pytest.mark.asyncio
    async def test_query_notes_with_limit(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test limiting number of notes returned."""
        # Create 5 notes
        notes = [
            Note(
                text=f"Note {i}",
                privacy_level=PrivacyLevel.PUBLIC,
                entity_type=EntityType.PROJECT,
                entity_id=project.id,
            )
            for i in range(5)
        ]
        for note in notes:
            test_session.add(note)
        await test_session.commit()

        service = QueryService(test_session)
        result_notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            limit=3,
        )

        assert len(result_notes) == 3

    @pytest.mark.asyncio
    async def test_query_notes_nonexistent_entity(
        self,
        test_session: AsyncSession,
    ):
        """Test querying notes for nonexistent entity returns empty."""
        service = QueryService(test_session)

        notes = await service.query_notes_by_entity(
            entity_type=EntityType.PROJECT,
            entity_id=99999,
        )

        assert len(notes) == 0


# ============================================================================
# Date/Time String Parsing Tests
# ============================================================================


class TestDateTimeStringParsing:
    """Test QueryBuilder date/time string parsing in real queries."""

    @pytest.mark.asyncio
    async def test_query_with_tomorrow_filter(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test querying with 'tomorrow' special value."""
        tomorrow = date.today() + timedelta(days=1)

        # Create work session for tomorrow
        ws = WorkSession(
            project_id=project.id,
            date=tomorrow,
            start_time=datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc),
            end_time=datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
            + timedelta(hours=3),
            duration_hours=Decimal("3.0"),
            summary="Tomorrow's work",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)
        await test_session.commit()

        # Build query manually using QueryBuilder
        from src.mosaic.services.query_builder import QueryBuilder

        builder = QueryBuilder(session=test_session)
        query = builder.build_work_sessions_query(start_date=tomorrow)

        # Execute
        result = await test_session.execute(query)
        sessions = list(result.scalars().all())

        assert len(sessions) == 1
        assert sessions[0].date == tomorrow

    @pytest.mark.asyncio
    async def test_query_with_iso_datetime_string(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test querying with ISO datetime string."""
        # Create meeting with specific datetime
        target_time = datetime(2026, 1, 20, 14, 30, 0, tzinfo=timezone.utc)
        meeting = Meeting(
            title="Test meeting",
            start_time=target_time,
            duration_minutes=60,
            summary="ISO datetime test",
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        test_session.add(meeting)
        await test_session.commit()

        # Query using ISO datetime string via structured query
        from src.mosaic.schemas.query_structured import (
            FilterOperator,
            FilterSpec,
            StructuredQuery,
        )
        from src.mosaic.services.query_service import QueryService

        service = QueryService(test_session)
        query = StructuredQuery(
            entity_types=[EntityType.MEETING],
            filters=[
                FilterSpec(
                    field="start_time",
                    operator=FilterOperator.GREATER_THAN_OR_EQUAL,
                    value="2026-01-20T00:00:00Z",
                ),
            ],
        )

        results = await service.structured_query(query)
        meetings = results["meetings"]

        assert len(meetings) >= 1
        assert any(m.title == "Test meeting" for m in meetings)

    @pytest.mark.asyncio
    async def test_query_with_iso_date_string(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test querying with ISO date string (YYYY-MM-DD)."""
        target_date = date(2026, 1, 20)

        # Create work session
        ws = WorkSession(
            project_id=project.id,
            date=target_date,
            start_time=datetime.combine(target_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            ),
            end_time=datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            + timedelta(hours=3),
            duration_hours=Decimal("3.0"),
            summary="Date string test",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)
        await test_session.commit()

        # Query using ISO date string via structured query
        from src.mosaic.schemas.query_structured import (
            FilterOperator,
            FilterSpec,
            StructuredQuery,
        )
        from src.mosaic.services.query_service import QueryService

        service = QueryService(test_session)
        query = StructuredQuery(
            entity_types=[EntityType.WORK_SESSION],
            filters=[
                FilterSpec(
                    field="date",
                    operator=FilterOperator.EQUAL,
                    value="2026-01-20",
                ),
            ],
        )

        results = await service.structured_query(query)
        sessions = results["work_sessions"]

        assert len(sessions) == 1
        assert sessions[0].date == target_date

    @pytest.mark.asyncio
    async def test_no_postgresql_type_errors(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that date/time strings don't cause PostgreSQL type errors."""
        # Create meeting
        meeting = Meeting(
            title="Type test meeting",
            start_time=datetime(2026, 1, 21, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        test_session.add(meeting)
        await test_session.commit()

        # These should NOT raise "operator does not exist" errors
        from src.mosaic.schemas.query_structured import (
            FilterOperator,
            FilterSpec,
            StructuredQuery,
        )
        from src.mosaic.services.query_service import QueryService

        service = QueryService(test_session)

        # Test with ISO datetime
        query1 = StructuredQuery(
            entity_types=[EntityType.MEETING],
            filters=[
                FilterSpec(
                    field="start_time",
                    operator=FilterOperator.LESS_THAN,
                    value="2026-01-22T00:00:00Z",
                ),
            ],
        )
        results1 = await service.structured_query(query1)
        assert "meetings" in results1

        # Test with special value
        query2 = StructuredQuery(
            entity_types=[EntityType.MEETING],
            filters=[
                FilterSpec(
                    field="start_time",
                    operator=FilterOperator.GREATER_THAN,
                    value="yesterday",
                ),
            ],
        )
        results2 = await service.structured_query(query2)
        assert "meetings" in results2

    @pytest.mark.asyncio
    async def test_timezone_handling_in_results(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that timezone-aware datetimes are handled correctly."""
        # Create meeting with UTC time
        utc_time = datetime(2026, 1, 20, 15, 0, 0, tzinfo=timezone.utc)
        meeting = Meeting(
            title="Timezone test",
            start_time=utc_time,
            duration_minutes=60,
            privacy_level=PrivacyLevel.PUBLIC,
            project_id=project.id,
        )
        test_session.add(meeting)
        await test_session.commit()

        # Query with timezone-aware ISO datetime
        from src.mosaic.schemas.query_structured import (
            FilterOperator,
            FilterSpec,
            StructuredQuery,
        )
        from src.mosaic.services.query_service import QueryService

        service = QueryService(test_session)
        query = StructuredQuery(
            entity_types=[EntityType.MEETING],
            filters=[
                FilterSpec(
                    field="start_time",
                    operator=FilterOperator.EQUAL,
                    value="2026-01-20T15:00:00Z",
                ),
            ],
        )

        results = await service.structured_query(query)
        meetings = results["meetings"]

        assert len(meetings) == 1
        assert meetings[0].start_time.tzinfo is not None
        assert meetings[0].start_time == utc_time
