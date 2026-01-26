"""Work session service with business logic for time tracking."""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import PrivacyLevel
from ..models.work_session import WorkSession
from .time_utils import validate_duration_hours


class WorkSessionService:
    """Business logic for work session operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize work session service.

        Args:
            session: Async database session
        """
        self.session = session

    async def create_work_session(
        self,
        project_id: int,
        date: date,
        duration_hours: Decimal,
        summary: Optional[str] = None,
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        tags: Optional[list[str]] = None,
    ) -> WorkSession:
        """
        Create work session with date and duration.

        Args:
            project_id: Project the work was done for
            date: Which day the work happened
            duration_hours: How many hours worked
            summary: Optional description of work done
            privacy_level: Privacy level (defaults to PRIVATE)
            tags: Optional tags for categorization

        Returns:
            WorkSession: Created work session

        Raises:
            ValueError: If duration is invalid
        """
        # Validate duration
        validate_duration_hours(duration_hours)

        # Create work session
        work_session = WorkSession(
            project_id=project_id,
            date=date,
            duration_hours=duration_hours,
            summary=summary,
            privacy_level=privacy_level,
            tags=tags or [],
        )

        self.session.add(work_session)
        await self.session.flush()
        await self.session.refresh(work_session)

        return work_session

    async def update_work_session(
        self,
        work_session_id: int,
        project_id: Optional[int] = None,
        date: Optional[date] = None,
        duration_hours: Optional[Decimal] = None,
        summary: Optional[str] = None,
        privacy_level: Optional[PrivacyLevel] = None,
        tags: Optional[list[str]] = None,
    ) -> WorkSession:
        """
        Update work session fields.

        Args:
            work_session_id: ID of work session to update
            project_id: New project ID (optional)
            date: New date (optional)
            duration_hours: New duration (optional)
            summary: New summary (optional)
            privacy_level: New privacy level (optional)
            tags: New tags (optional)

        Returns:
            WorkSession: Updated work session

        Raises:
            ValueError: If work session not found or duration invalid
        """
        # Validate duration if provided
        if duration_hours is not None:
            validate_duration_hours(duration_hours)

        # Fetch existing work session
        result = await self.session.execute(
            select(WorkSession).where(WorkSession.id == work_session_id)
        )
        work_session = result.scalar_one_or_none()

        if work_session is None:
            raise ValueError(f"WorkSession with id {work_session_id} not found")

        # Update fields
        if project_id is not None:
            work_session.project_id = project_id

        if date is not None:
            work_session.date = date

        if duration_hours is not None:
            work_session.duration_hours = duration_hours

        if summary is not None:
            work_session.summary = summary

        if privacy_level is not None:
            work_session.privacy_level = privacy_level

        if tags is not None:
            work_session.tags = tags

        await self.session.flush()
        await self.session.refresh(work_session)

        return work_session

    async def generate_timecard(
        self,
        start_date: date,
        end_date: date,
        include_private: bool = True,
        project_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate timecard data by project and date.

        Multiple sessions on same project/date are merged with
        summaries combined.

        Args:
            start_date: Start of timecard period (inclusive)
            end_date: End of timecard period (inclusive)
            include_private: Whether to include private sessions
                (default: True)
            project_id: Optional filter to specific project

        Returns:
            list[dict]: Timecard entries with aggregated data
                Each dict contains:
                - date: Session date
                - project_id: Project ID
                - total_hours: Sum of all session hours for project/date
                - summary: Combined summaries (newline separated)

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError("end_date must be after or equal to start_date")

        # Build query
        query = (
            select(
                WorkSession.date,
                WorkSession.project_id,
                func.sum(WorkSession.duration_hours).label("total_hours"),
                func.string_agg(WorkSession.summary, "\n").label("summary"),
            )
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
            .group_by(WorkSession.date, WorkSession.project_id)
            .order_by(WorkSession.date, WorkSession.project_id)
        )

        # Apply privacy filter
        if not include_private:
            query = query.where(WorkSession.privacy_level != PrivacyLevel.PRIVATE)

        # Apply project filter
        if project_id is not None:
            query = query.where(WorkSession.project_id == project_id)

        # Execute query
        result = await self.session.execute(query)
        rows = result.all()

        # Convert to list of dicts
        timecard = []
        for row in rows:
            timecard.append(
                {
                    "date": row.date,
                    "project_id": row.project_id,
                    "total_hours": row.total_hours,
                    "summary": row.summary if row.summary else "",
                }
            )

        return timecard

    async def get_work_session(self, work_session_id: int) -> Optional[WorkSession]:
        """
        Get work session by ID.

        Args:
            work_session_id: Work session ID

        Returns:
            WorkSession if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkSession).where(WorkSession.id == work_session_id)
        )
        return result.scalar_one_or_none()

    async def delete_work_session(self, work_session_id: int) -> bool:
        """
        Delete work session.

        Args:
            work_session_id: Work session ID to delete

        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.session.execute(
            select(WorkSession).where(WorkSession.id == work_session_id)
        )
        work_session = result.scalar_one_or_none()

        if work_session is None:
            return False

        await self.session.delete(work_session)
        await self.session.flush()

        return True
