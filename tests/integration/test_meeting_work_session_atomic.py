"""Integration tests for atomic meeting + work session creation.

CRITICAL: These tests verify that meeting and work session are created
atomically - both succeed or both fail.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.meeting import Meeting
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.services.meeting_service import MeetingService


class TestMeetingWorkSessionAtomic:
    """Test atomic creation of meeting + work session."""

    @pytest.fixture
    async def meeting_service(self, session: AsyncSession) -> MeetingService:
        """Create meeting service."""
        return MeetingService(session)

    @pytest.mark.asyncio
    async def test_create_meeting_with_work_session_success(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test successful atomic creation of meeting + work session."""
        start_time = datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        duration_minutes = 60

        meeting, work_session = await meeting_service.create_meeting_with_work_session(
            start_time=start_time,
            duration_minutes=duration_minutes,
            project_id=project.id,
            title="Project Kickoff",
            summary="Project kickoff meeting",
            privacy_level=PrivacyLevel.INTERNAL,
        )

        # Verify both entities were created
        assert meeting.id is not None
        assert work_session.id is not None

        # Verify meeting details
        assert meeting.start_time == start_time
        assert meeting.duration_minutes == duration_minutes
        assert meeting.title == "Project Kickoff"
        assert meeting.summary == "Project kickoff meeting"
        assert meeting.privacy_level == PrivacyLevel.INTERNAL
        assert meeting.project_id == project.id

        # Verify work session details
        assert work_session.project_id == project.id
        assert work_session.date == start_time.date()
        assert work_session.duration_hours > 0
        assert work_session.summary == "Project kickoff meeting"
        assert work_session.privacy_level == PrivacyLevel.INTERNAL

    @pytest.mark.asyncio
    async def test_meeting_work_session_same_transaction(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test that meeting and work session are in same transaction."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        # Create meeting + work session
        meeting, work_session = await meeting_service.create_meeting_with_work_session(
            start_time=start_time,
            duration_minutes=90,
            project_id=project.id,
            title="Team Sync",
        )

        # Both should be flushed to database
        await session.commit()

        # Query database to verify both exist
        meeting_result = await session.execute(select(Meeting).where(Meeting.id == meeting.id))
        db_meeting = meeting_result.scalar_one_or_none()
        assert db_meeting is not None

        ws_result = await session.execute(
            select(WorkSession).where(WorkSession.id == work_session.id)
        )
        db_ws = ws_result.scalar_one_or_none()
        assert db_ws is not None

    @pytest.mark.asyncio
    async def test_work_session_duration_exact(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test that work session duration is calculated exactly from meeting duration."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        # 45 minutes = 0.75 hours (exact, no rounding)
        meeting, work_session = await meeting_service.create_meeting_with_work_session(
            start_time=start_time,
            duration_minutes=45,
            project_id=project.id,
            title="Short Meeting",
        )

        assert float(work_session.duration_hours) == pytest.approx(0.75, abs=0.01)

        # 30 minutes = 0.5 hours (exact)
        meeting2, work_session2 = await meeting_service.create_meeting_with_work_session(
            start_time=start_time,
            duration_minutes=30,
            project_id=project.id,
            title="Quick Sync",
        )

        assert float(work_session2.duration_hours) == pytest.approx(0.5, abs=0.01)

    @pytest.mark.asyncio
    async def test_invalid_project_raises_error(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
    ):
        """Test that invalid project ID raises ValueError."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="Project with id 999999 not found"):
            await meeting_service.create_meeting_with_work_session(
                start_time=start_time,
                duration_minutes=60,
                project_id=999999,
                title="Invalid Project Meeting",
            )

        # Verify no meeting or work session was created
        meeting_count = await session.execute(select(Meeting))
        assert len(list(meeting_count.scalars().all())) == 0

        ws_count = await session.execute(select(WorkSession))
        assert len(list(ws_count.scalars().all())) == 0

    @pytest.mark.asyncio
    async def test_negative_duration_raises_error(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test that negative duration raises ValueError."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            await meeting_service.create_meeting_with_work_session(
                start_time=start_time,
                duration_minutes=-30,
                project_id=project.id,
                title="Negative Duration Meeting",
            )

    @pytest.mark.asyncio
    async def test_zero_duration_raises_error(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test that zero duration raises ValueError."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            await meeting_service.create_meeting_with_work_session(
                start_time=start_time,
                duration_minutes=0,
                project_id=project.id,
                title="Zero Duration Meeting",
            )

    @pytest.mark.asyncio
    async def test_rollback_on_error(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test that transaction rolls back on error (both entities removed)."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        # Attempt to create with invalid project
        try:
            await meeting_service.create_meeting_with_work_session(
                start_time=start_time,
                duration_minutes=60,
                project_id=999999,
                title="Rollback Test Meeting",
            )
        except ValueError:
            pass

        await session.rollback()

        # Verify no entities were created
        meeting_result = await session.execute(select(Meeting))
        meetings = list(meeting_result.scalars().all())
        assert len(meetings) == 0

        ws_result = await session.execute(select(WorkSession))
        work_sessions = list(ws_result.scalars().all())
        assert len(work_sessions) == 0

    @pytest.mark.asyncio
    async def test_meeting_without_work_session_creates_only_meeting(
        self,
        meeting_service: MeetingService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating meeting without work session (separate method)."""
        start_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        meeting = await meeting_service.create_meeting(
            start_time=start_time,
            duration_minutes=60,
            project_id=project.id,
            title="Standalone Meeting",
        )

        assert meeting.id is not None

        # Verify no work session was created
        ws_result = await session.execute(select(WorkSession))
        work_sessions = list(ws_result.scalars().all())
        assert len(work_sessions) == 0
