"""Unit tests for MeetingRepository with attendee management."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.meeting import Meeting
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project
from src.mosaic.repositories.meeting_repository import MeetingRepository


class TestMeetingRepositoryBasicQueries:
    """Test basic MeetingRepository query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> MeetingRepository:
        """Create meeting repository."""
        return MeetingRepository(session)

    async def test_list_by_project(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test listing meetings for a project."""
        # Create meetings for project
        meeting1 = Meeting(
            title="Sprint Planning",
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            project_id=project.id,
        )
        meeting2 = Meeting(
            title="Sprint Review",
            start_time=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            project_id=project.id,
        )
        session.add_all([meeting1, meeting2])
        await session.flush()

        # List by project
        results = await repo.list_by_project(project.id)

        assert len(results) == 2
        titles = {m.title for m in results}
        assert "Sprint Planning" in titles
        assert "Sprint Review" in titles

    async def test_list_by_date_range(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test listing meetings in time range."""
        # Create meetings across multiple days
        meeting1 = Meeting(
            title="Early Meeting",
            start_time=datetime(2024, 1, 10, 9, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        meeting2 = Meeting(
            title="Mid Meeting",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        meeting3 = Meeting(
            title="Late Meeting",
            start_time=datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        session.add_all([meeting1, meeting2, meeting3])
        await session.flush()

        # Query date range (Jan 12-18 should get only mid meeting)
        results = await repo.list_by_date_range(
            datetime(2024, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 18, 23, 59, tzinfo=timezone.utc),
        )

        assert len(results) == 1
        assert results[0].title == "Mid Meeting"

    async def test_list_by_date_range_invalid_raises_error(self, repo: MeetingRepository):
        """Test date range with end before start raises ValueError."""
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            await repo.list_by_date_range(
                datetime(2024, 1, 20, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 10, 0, 0, tzinfo=timezone.utc),
            )

    async def test_get_by_id_with_attendees(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        project: Project,
        person: Person,
    ):
        """Test eager loading attendees."""
        # Create meeting
        meeting = Meeting(
            title="Team Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            project_id=project.id,
        )
        session.add(meeting)
        await session.flush()

        # Add attendee
        await repo.add_attendee(meeting.id, person.id)

        # Get with attendees
        result = await repo.get_by_id_with_attendees(meeting.id)

        assert result is not None
        assert result.id == meeting.id
        assert len(result.attendees) == 1
        assert result.attendees[0].person_id == person.id

    async def test_get_by_id_with_full_details(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        project: Project,
        person: Person,
    ):
        """Test eager loading all relations (project and attendees)."""
        # Create meeting
        meeting = Meeting(
            title="Full Details Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            project_id=project.id,
        )
        session.add(meeting)
        await session.flush()

        # Add attendee
        await repo.add_attendee(meeting.id, person.id)

        # Get with full details
        result = await repo.get_by_id_with_full_details(meeting.id)

        assert result is not None
        assert result.project is not None
        assert result.project.name == project.name
        assert len(result.attendees) == 1
        assert result.attendees[0].person is not None
        assert result.attendees[0].person.full_name == person.full_name


class TestMeetingRepositoryAttendeeManagement:
    """Test attendee management methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> MeetingRepository:
        """Create meeting repository."""
        return MeetingRepository(session)

    @pytest.fixture
    async def test_meeting(self, session: AsyncSession) -> Meeting:
        """Create test meeting."""
        meeting = Meeting(
            title="Test Meeting",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        session.add(meeting)
        await session.flush()
        await session.refresh(meeting)
        return meeting

    async def test_add_attendee(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        test_meeting: Meeting,
        person: Person,
    ):
        """Test adding attendee to meeting."""
        attendee = await repo.add_attendee(test_meeting.id, person.id)

        assert attendee.id is not None
        assert attendee.meeting_id == test_meeting.id
        assert attendee.person_id == person.id

    async def test_add_multiple_attendees(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        test_meeting: Meeting,
    ):
        """Test adding multiple attendees to meeting."""
        # Create two people
        person1 = Person(full_name="Person 1", email="person1@example.com")
        person2 = Person(full_name="Person 2", email="person2@example.com")
        session.add_all([person1, person2])
        await session.flush()

        # Add both as attendees
        await repo.add_attendee(test_meeting.id, person1.id)
        await repo.add_attendee(test_meeting.id, person2.id)

        # Get attendees
        attendees = await repo.get_attendees(test_meeting.id)

        assert len(attendees) == 2
        person_ids = {a.person_id for a in attendees}
        assert person1.id in person_ids
        assert person2.id in person_ids

    async def test_remove_attendee(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        test_meeting: Meeting,
        person: Person,
    ):
        """Test removing attendee from meeting."""
        # Add attendee
        await repo.add_attendee(test_meeting.id, person.id)

        # Remove attendee
        result = await repo.remove_attendee(test_meeting.id, person.id)

        assert result is True

        # Verify removed
        attendees = await repo.get_attendees(test_meeting.id)
        assert len(attendees) == 0

    async def test_remove_nonexistent_attendee(
        self, repo: MeetingRepository, test_meeting: Meeting
    ):
        """Test removing non-existent attendee returns False."""
        result = await repo.remove_attendee(test_meeting.id, 999999)
        assert result is False

    async def test_get_attendees(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        test_meeting: Meeting,
    ):
        """Test getting all attendees for a meeting."""
        # Create people
        person1 = Person(full_name="Alice")
        person2 = Person(full_name="Bob")
        session.add_all([person1, person2])
        await session.flush()

        # Add attendees
        await repo.add_attendee(test_meeting.id, person1.id)
        await repo.add_attendee(test_meeting.id, person2.id)

        # Get attendees with person data
        attendees = await repo.get_attendees(test_meeting.id)

        assert len(attendees) == 2
        # Verify person data is eagerly loaded
        names = {a.person.full_name for a in attendees}
        assert "Alice" in names
        assert "Bob" in names

    async def test_list_by_attendee(
        self,
        repo: MeetingRepository,
        session: AsyncSession,
        person: Person,
    ):
        """Test listing all meetings a person attended."""
        # Create multiple meetings
        meeting1 = Meeting(
            title="Meeting 1",
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        meeting2 = Meeting(
            title="Meeting 2",
            start_time=datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        meeting3 = Meeting(
            title="Meeting 3",
            start_time=datetime(2024, 1, 17, 11, 0, tzinfo=timezone.utc),
            duration_minutes=60,
        )
        session.add_all([meeting1, meeting2, meeting3])
        await session.flush()

        # Add person to meeting1 and meeting2 only
        await repo.add_attendee(meeting1.id, person.id)
        await repo.add_attendee(meeting2.id, person.id)

        # List meetings for person
        results = await repo.list_by_attendee(person.id)

        assert len(results) == 2
        titles = {m.title for m in results}
        assert "Meeting 1" in titles
        assert "Meeting 2" in titles
        assert "Meeting 3" not in titles
