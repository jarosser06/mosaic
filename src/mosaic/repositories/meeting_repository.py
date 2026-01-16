"""Meeting repository with attendee management."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.meeting import Meeting, MeetingAttendee
from .base import BaseRepository


class MeetingRepository(BaseRepository[Meeting]):
    """Repository for Meeting operations with attendee management."""

    def __init__(self, session: AsyncSession):
        """
        Initialize meeting repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Meeting)

    async def get_by_id_with_attendees(self, id: int) -> Optional[Meeting]:
        """
        Get meeting by ID with attendees eagerly loaded.

        Args:
            id: Meeting ID

        Returns:
            Optional[Meeting]: Meeting with attendees if found, None otherwise
        """
        result = await self.session.execute(
            select(Meeting).where(Meeting.id == id).options(selectinload(Meeting.attendees))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_full_details(self, id: int) -> Optional[Meeting]:
        """
        Get meeting by ID with all relations eagerly loaded.

        Args:
            id: Meeting ID

        Returns:
            Optional[Meeting]: Meeting with project and attendees if found, None otherwise
        """
        result = await self.session.execute(
            select(Meeting)
            .where(Meeting.id == id)
            .options(
                joinedload(Meeting.project),
                selectinload(Meeting.attendees).selectinload(MeetingAttendee.person),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: int) -> list[Meeting]:
        """
        List all meetings for a project.

        Args:
            project_id: Project ID

        Returns:
            list[Meeting]: All meetings for this project
        """
        result = await self.session.execute(select(Meeting).where(Meeting.project_id == project_id))
        return list(result.scalars().all())

    async def list_by_date_range(self, start_time: datetime, end_time: datetime) -> list[Meeting]:
        """
        List meetings in a time range.

        Args:
            start_time: Range start time (inclusive)
            end_time: Range end time (inclusive)

        Returns:
            list[Meeting]: Meetings in time range

        Raises:
            ValueError: If end_time is before start_time
        """
        if end_time < start_time:
            raise ValueError("end_time must be after start_time")

        result = await self.session.execute(
            select(Meeting)
            .where(Meeting.start_time >= start_time)
            .where(Meeting.start_time <= end_time)
        )
        return list(result.scalars().all())

    async def list_by_attendee(self, person_id: int) -> list[Meeting]:
        """
        List all meetings a person attended.

        Args:
            person_id: Person ID

        Returns:
            list[Meeting]: All meetings this person attended
        """
        result = await self.session.execute(
            select(Meeting).join(MeetingAttendee).where(MeetingAttendee.person_id == person_id)
        )
        return list(result.scalars().all())

    async def add_attendee(self, meeting_id: int, person_id: int) -> MeetingAttendee:
        """
        Add an attendee to a meeting.

        Args:
            meeting_id: Meeting ID
            person_id: Person ID

        Returns:
            MeetingAttendee: Created attendee record

        Raises:
            IntegrityError: If person or meeting does not exist, or attendee already exists
        """
        attendee = MeetingAttendee(meeting_id=meeting_id, person_id=person_id)
        self.session.add(attendee)
        await self.session.flush()
        await self.session.refresh(attendee)
        return attendee

    async def remove_attendee(self, meeting_id: int, person_id: int) -> bool:
        """
        Remove an attendee from a meeting.

        Args:
            meeting_id: Meeting ID
            person_id: Person ID

        Returns:
            bool: True if attendee was removed, False if not found
        """
        result = await self.session.execute(
            select(MeetingAttendee)
            .where(MeetingAttendee.meeting_id == meeting_id)
            .where(MeetingAttendee.person_id == person_id)
        )
        attendee = result.scalar_one_or_none()

        if not attendee:
            return False

        await self.session.delete(attendee)
        await self.session.flush()
        return True

    async def get_attendees(self, meeting_id: int) -> list[MeetingAttendee]:
        """
        Get all attendees for a meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            list[MeetingAttendee]: All attendees for this meeting
        """
        result = await self.session.execute(
            select(MeetingAttendee)
            .where(MeetingAttendee.meeting_id == meeting_id)
            .options(selectinload(MeetingAttendee.person))
        )
        return list(result.scalars().all())
