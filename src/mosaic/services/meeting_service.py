"""Meeting service with business logic for meeting management."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import PrivacyLevel
from ..models.meeting import Meeting, MeetingAttendee
from ..models.project import Project
from ..models.work_session import WorkSession


class MeetingService:
    """Business logic for meeting operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize meeting service.

        Args:
            session: Async database session
        """
        self.session = session

    async def create_meeting(
        self,
        start_time: datetime,
        duration_minutes: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        project_id: Optional[int] = None,
        meeting_type: Optional[str] = None,
        location: Optional[str] = None,
        attendee_ids: Optional[list[int]] = None,
        tags: Optional[list[str]] = None,
    ) -> Meeting:
        """
        Create meeting without automatic work session.

        Args:
            start_time: When meeting starts
            duration_minutes: Meeting duration in minutes
            title: Optional meeting title
            summary: Optional meeting description
            privacy_level: Privacy level (defaults to PRIVATE)
            project_id: Optional associated project
            meeting_type: Optional meeting type
            location: Optional meeting location
            attendee_ids: Optional list of person IDs attending
            tags: Optional tags for categorization

        Returns:
            Meeting: Created meeting

        Raises:
            ValueError: If duration_minutes is not positive
        """
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        # Create meeting
        meeting = Meeting(
            start_time=start_time,
            duration_minutes=duration_minutes,
            title=title,
            summary=summary,
            privacy_level=privacy_level,
            project_id=project_id,
            meeting_type=meeting_type,
            location=location,
            tags=tags or [],
        )

        self.session.add(meeting)
        await self.session.flush()

        # Add attendees if provided
        if attendee_ids:
            for person_id in attendee_ids:
                attendee = MeetingAttendee(
                    meeting_id=meeting.id,
                    person_id=person_id,
                )
                self.session.add(attendee)

        await self.session.flush()
        await self.session.refresh(meeting)

        return meeting

    async def create_meeting_with_work_session(
        self,
        start_time: datetime,
        duration_minutes: int,
        project_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        meeting_type: Optional[str] = None,
        location: Optional[str] = None,
        attendee_ids: Optional[list[int]] = None,
        tags: Optional[list[str]] = None,
    ) -> tuple[Meeting, WorkSession]:
        """
        Create meeting and work session atomically.

        CRITICAL: Both entities created in same transaction -
        both succeed or both fail.
        WorkSession inherits on_behalf_of from project.

        Args:
            start_time: When meeting starts
            duration_minutes: Meeting duration in minutes
            project_id: Associated project (REQUIRED for this method)
            title: Optional meeting title
            summary: Optional meeting description
            privacy_level: Privacy level (defaults to PRIVATE)
            meeting_type: Optional meeting type
            location: Optional meeting location
            attendee_ids: Optional list of person IDs attending
            tags: Optional tags for categorization

        Returns:
            tuple[Meeting, WorkSession]: Created meeting and work session

        Raises:
            ValueError: If duration_minutes is not positive or
                project not found
        """
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        # Verify project exists
        project_result = await self.session.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()

        if project is None:
            raise ValueError(f"Project with id {project_id} not found")

        # Create meeting
        meeting = Meeting(
            start_time=start_time,
            duration_minutes=duration_minutes,
            title=title,
            summary=summary,
            privacy_level=privacy_level,
            project_id=project_id,
            meeting_type=meeting_type,
            location=location,
            tags=tags or [],
        )

        self.session.add(meeting)
        await self.session.flush()

        # Add attendees if provided
        if attendee_ids:
            for person_id in attendee_ids:
                attendee = MeetingAttendee(
                    meeting_id=meeting.id,
                    person_id=person_id,
                )
                self.session.add(attendee)

        # Calculate duration in hours from meeting duration_minutes
        # Convert minutes to hours (exact conversion, no rounding)
        duration_hours = Decimal(str(duration_minutes)) / Decimal("60")

        # Create work session with same details
        # Note: Meetings still have times, but work sessions only store date + duration
        work_session = WorkSession(
            project_id=project_id,
            date=start_time.date(),
            duration_hours=duration_hours,
            summary=summary,  # Inherit summary from meeting
            privacy_level=privacy_level,  # Inherit privacy level
            tags=tags or [],  # Inherit tags from meeting
        )

        self.session.add(work_session)
        await self.session.flush()

        # Refresh both entities to get full data
        await self.session.refresh(meeting)
        await self.session.refresh(work_session)

        return meeting, work_session

    async def update_meeting(
        self,
        meeting_id: int,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        privacy_level: Optional[PrivacyLevel] = None,
        project_id: Optional[int] = None,
        meeting_type: Optional[str] = None,
        location: Optional[str] = None,
        attendee_ids: Optional[list[int]] = None,
        tags: Optional[list[str]] = None,
    ) -> Meeting:
        """
        Update meeting.

        Args:
            meeting_id: Meeting ID to update
            start_time: New start time (optional)
            duration_minutes: New duration (optional)
            title: New title (optional)
            summary: New summary (optional)
            privacy_level: New privacy level (optional)
            project_id: New project ID (optional)
            meeting_type: New meeting type (optional)
            location: New location (optional)
            attendee_ids: New list of attendee person IDs
                (optional, replaces existing)
            tags: New tags (optional, replaces existing)

        Returns:
            Meeting: Updated meeting

        Raises:
            ValueError: If meeting not found or duration_minutes invalid
        """
        # Fetch existing meeting
        result = await self.session.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()

        if meeting is None:
            raise ValueError(f"Meeting with id {meeting_id} not found")

        # Update fields
        if start_time is not None:
            meeting.start_time = start_time

        if duration_minutes is not None:
            if duration_minutes <= 0:
                raise ValueError("duration_minutes must be positive")
            meeting.duration_minutes = duration_minutes

        if title is not None:
            meeting.title = title

        if summary is not None:
            meeting.summary = summary

        if privacy_level is not None:
            meeting.privacy_level = privacy_level

        if project_id is not None:
            meeting.project_id = project_id

        if meeting_type is not None:
            meeting.meeting_type = meeting_type

        if location is not None:
            meeting.location = location

        if tags is not None:
            meeting.tags = tags

        # Handle attendees update
        if attendee_ids is not None:
            # Delete existing attendees
            existing_attendees = await self.session.execute(
                select(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting_id)
            )
            for attendee in existing_attendees.scalars().all():
                await self.session.delete(attendee)

            # Add new attendees
            for person_id in attendee_ids:
                attendee = MeetingAttendee(
                    meeting_id=meeting_id,
                    person_id=person_id,
                )
                self.session.add(attendee)

        await self.session.flush()
        await self.session.refresh(meeting)

        return meeting

    async def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        """
        Get meeting by ID.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting if found, None otherwise
        """
        result = await self.session.execute(select(Meeting).where(Meeting.id == meeting_id))
        return result.scalar_one_or_none()

    async def delete_meeting(self, meeting_id: int) -> bool:
        """
        Delete meeting.

        Args:
            meeting_id: Meeting ID to delete

        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.session.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()

        if meeting is None:
            return False

        await self.session.delete(meeting)
        await self.session.flush()

        return True
