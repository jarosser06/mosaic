"""Tests for Meeting and MeetingAttendee models."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.meeting import Meeting, MeetingAttendee
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project


@pytest.mark.asyncio
async def test_meeting_creation_minimal(session: AsyncSession) -> None:
    """Test creating meeting with minimal required fields."""
    start_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)

    meeting = Meeting(
        title="Team Standup",
        start_time=start_time,
        duration_minutes=60,
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.id is not None
    assert meeting.title == "Team Standup"
    assert meeting.start_time == start_time
    assert meeting.duration_minutes == 60
    assert meeting.privacy_level == PrivacyLevel.PRIVATE
    assert meeting.project_id is None
    assert meeting.summary is None
    assert meeting.meeting_type is None
    assert meeting.location is None
    assert meeting.created_at is not None
    assert meeting.updated_at is not None


@pytest.mark.asyncio
async def test_meeting_creation_full(session: AsyncSession, project: Project) -> None:
    """Test creating meeting with all fields populated."""
    meeting = Meeting(
        title="Sprint Planning",
        start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        duration_minutes=90,
        summary="Sprint planning meeting",
        privacy_level=PrivacyLevel.INTERNAL,
        project_id=project.id,
        meeting_type="planning",
        location="Conference Room A",
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.title == "Sprint Planning"
    assert meeting.summary == "Sprint planning meeting"
    assert meeting.privacy_level == PrivacyLevel.INTERNAL
    assert meeting.project_id == project.id
    assert meeting.meeting_type == "planning"
    assert meeting.location == "Conference Room A"


@pytest.mark.parametrize(
    "privacy_level",
    [PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL, PrivacyLevel.PRIVATE],
)
@pytest.mark.asyncio
async def test_meeting_privacy_levels(session: AsyncSession, privacy_level: PrivacyLevel) -> None:
    """Test all privacy level values for meetings."""
    meeting = Meeting(
        title="Test Meeting",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=30,
        privacy_level=privacy_level,
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.privacy_level == privacy_level


@pytest.mark.asyncio
async def test_meeting_with_project(session: AsyncSession, project: Project) -> None:
    """Test meeting associated with a project."""
    meeting = Meeting(
        title="Project Kickoff",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        project_id=project.id,
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.project_id == project.id


@pytest.mark.asyncio
async def test_meeting_without_project(session: AsyncSession) -> None:
    """Test meeting without project association."""
    meeting = Meeting(
        title="General Discussion",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=30,
        project_id=None,
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.project_id is None


@pytest.mark.asyncio
async def test_meeting_attendee_creation(session: AsyncSession, person: Person) -> None:
    """Test creating meeting attendee."""
    meeting = Meeting(
        title="Team Sync",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
    )
    session.add(meeting)
    await session.flush()

    attendee = MeetingAttendee(
        meeting_id=meeting.id,
        person_id=person.id,
    )
    session.add(attendee)
    await session.flush()
    await session.refresh(attendee)

    assert attendee.id is not None
    assert attendee.meeting_id == meeting.id
    assert attendee.person_id == person.id


@pytest.mark.asyncio
async def test_meeting_relationship_with_attendees(session: AsyncSession, person: Person) -> None:
    """Test meeting-attendees relationship loading."""
    person2 = Person(full_name="Jane Smith", email="jane@example.com")
    session.add(person2)
    await session.flush()

    meeting = Meeting(
        title="Team Meeting",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
    )
    session.add(meeting)
    await session.flush()

    attendee1 = MeetingAttendee(meeting_id=meeting.id, person_id=person.id)
    attendee2 = MeetingAttendee(meeting_id=meeting.id, person_id=person2.id)
    session.add_all([attendee1, attendee2])
    await session.flush()

    # Reload with relationship
    stmt = (
        select(Meeting)
        .where(Meeting.id == meeting.id)
        .options(selectinload(Meeting.attendees).selectinload(MeetingAttendee.person))
    )
    result = await session.execute(stmt)
    loaded_meeting = result.scalar_one()

    assert len(loaded_meeting.attendees) == 2
    attendee_names = {a.person.full_name for a in loaded_meeting.attendees}
    assert attendee_names == {"John Doe", "Jane Smith"}


@pytest.mark.asyncio
async def test_meeting_attendee_cascade_delete(session: AsyncSession, person: Person) -> None:
    """Test that meeting attendees are deleted when meeting is deleted."""
    meeting = Meeting(
        title="Temporary Meeting",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
    )
    session.add(meeting)
    await session.flush()

    attendee = MeetingAttendee(meeting_id=meeting.id, person_id=person.id)
    session.add(attendee)
    await session.flush()

    attendee_id = attendee.id

    # Delete meeting
    await session.delete(meeting)
    await session.flush()

    # Attendee should be deleted
    stmt = select(MeetingAttendee).where(MeetingAttendee.id == attendee_id)
    result = await session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_meeting_relationship_with_project(session: AsyncSession, project: Project) -> None:
    """Test meeting-project relationship loading."""
    meeting = Meeting(
        title="Project Review",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        project_id=project.id,
    )
    session.add(meeting)
    await session.flush()

    # Reload with relationship
    stmt = select(Meeting).where(Meeting.id == meeting.id).options(selectinload(Meeting.project))
    result = await session.execute(stmt)
    loaded_meeting = result.scalar_one()

    assert loaded_meeting.project is not None
    assert loaded_meeting.project.name == project.name


@pytest.mark.asyncio
async def test_meeting_start_time_indexing(session: AsyncSession) -> None:
    """Test that meeting start times are indexed and queryable."""
    start1 = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
    start2 = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)
    start3 = datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc)

    meeting1 = Meeting(title="Morning Meeting", start_time=start1, duration_minutes=60)
    meeting2 = Meeting(title="Afternoon Meeting", start_time=start2, duration_minutes=30)
    meeting3 = Meeting(title="Next Day Meeting", start_time=start3, duration_minutes=60)
    session.add_all([meeting1, meeting2, meeting3])
    await session.flush()

    # Query by date range
    stmt = select(Meeting).where(
        Meeting.start_time >= datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc),
        Meeting.start_time < datetime(2024, 1, 16, 0, 0, tzinfo=timezone.utc),
    )
    result = await session.execute(stmt)
    meetings = result.scalars().all()

    assert len(meetings) == 2


@pytest.mark.parametrize(
    "duration",
    [15, 30, 45, 60, 90, 120],
)
@pytest.mark.asyncio
async def test_meeting_duration_values(session: AsyncSession, duration: int) -> None:
    """Test various meeting duration values."""
    meeting = Meeting(
        title="Test Duration Meeting",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=duration,
    )
    session.add(meeting)
    await session.flush()
    await session.refresh(meeting)

    assert meeting.duration_minutes == duration
