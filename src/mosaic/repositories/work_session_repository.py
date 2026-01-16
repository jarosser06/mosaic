"""Work session repository with timecard aggregation."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.base import PrivacyLevel
from ..models.work_session import WorkSession
from .base import BaseRepository


class TimecardEntry:
    """
    Data class for timecard aggregation results.

    Attributes:
        project_id: Project ID
        project_name: Project name
        date: Work date
        total_hours: Total hours worked (sum of duration_hours)
    """

    def __init__(self, project_id: int, project_name: str, date: date, total_hours: Decimal):
        """
        Initialize timecard entry.

        Args:
            project_id: Project ID
            project_name: Project name
            date: Work date
            total_hours: Total hours worked
        """
        self.project_id = project_id
        self.project_name = project_name
        self.date = date
        self.total_hours = total_hours


class WorkSessionRepository(BaseRepository[WorkSession]):
    """Repository for WorkSession operations with timecard aggregation."""

    def __init__(self, session: AsyncSession):
        """
        Initialize work session repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, WorkSession)

    async def get_by_id_with_project(self, id: int) -> Optional[WorkSession]:
        """
        Get work session by ID with project eagerly loaded.

        Args:
            id: Work session ID

        Returns:
            Optional[WorkSession]: Work session with project if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkSession).where(WorkSession.id == id).options(joinedload(WorkSession.project))
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: int) -> list[WorkSession]:
        """
        List all work sessions for a project.

        Args:
            project_id: Project ID

        Returns:
            list[WorkSession]: All work sessions for this project
        """
        result = await self.session.execute(
            select(WorkSession).where(WorkSession.project_id == project_id)
        )
        return list(result.scalars().all())

    async def list_by_date_range(self, start_date: date, end_date: date) -> list[WorkSession]:
        """
        List work sessions in a date range.

        Args:
            start_date: Range start date (inclusive)
            end_date: Range end date (inclusive)

        Returns:
            list[WorkSession]: Work sessions in date range

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError("end_date must be after start_date")

        result = await self.session.execute(
            select(WorkSession)
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
        )
        return list(result.scalars().all())

    async def list_by_project_and_date_range(
        self, project_id: int, start_date: date, end_date: date
    ) -> list[WorkSession]:
        """
        List work sessions for a project in a date range.

        Args:
            project_id: Project ID
            start_date: Range start date (inclusive)
            end_date: Range end date (inclusive)

        Returns:
            list[WorkSession]: Work sessions matching criteria

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError("end_date must be after start_date")

        result = await self.session.execute(
            select(WorkSession)
            .where(WorkSession.project_id == project_id)
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
        )
        return list(result.scalars().all())

    async def get_timecard_data(
        self,
        start_date: date,
        end_date: date,
        privacy_filter: Optional[PrivacyLevel] = None,
    ) -> list[TimecardEntry]:
        """
        Aggregate work sessions by project and date for timecard generation.

        This is the critical method for generating timecards. It groups work sessions
        by project_id and date, summing the duration_hours for each group.

        Args:
            start_date: Range start date (inclusive)
            end_date: Range end date (inclusive)
            privacy_filter: If specified, only include sessions at this
                privacy level or less restrictive

        Returns:
            list[TimecardEntry]: Aggregated timecard entries

        Raises:
            ValueError: If end_date is before start_date

        Example:
            >>> entries = await repo.get_timecard_data(
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 7),
            ...     privacy_filter=PrivacyLevel.PUBLIC
            ... )
            >>> for entry in entries:
            ...     print(f"{entry.project_name} on {entry.date}: {entry.total_hours}h")
        """
        if end_date < start_date:
            raise ValueError("end_date must be after start_date")

        # Import Project here to avoid circular import
        from ..models.project import Project

        # Build base query with aggregation
        query = (
            select(
                WorkSession.project_id,
                Project.name.label("project_name"),
                WorkSession.date,
                func.sum(WorkSession.duration_hours).label("total_hours"),
            )
            .join(Project, WorkSession.project_id == Project.id)
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
        )

        # Apply privacy filter if specified
        if privacy_filter is not None:
            # Privacy levels from least to most restrictive: PUBLIC < INTERNAL < PRIVATE
            # If filter is PUBLIC, include PUBLIC only
            # If filter is INTERNAL, include PUBLIC and INTERNAL
            # If filter is PRIVATE, include all
            if privacy_filter == PrivacyLevel.PUBLIC:
                query = query.where(WorkSession.privacy_level == PrivacyLevel.PUBLIC)
            elif privacy_filter == PrivacyLevel.INTERNAL:
                query = query.where(
                    WorkSession.privacy_level.in_([PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL])
                )
            # For PRIVATE, include all (no filter needed)

        # Group by project and date
        query = query.group_by(WorkSession.project_id, Project.name, WorkSession.date).order_by(
            WorkSession.date, Project.name
        )

        result = await self.session.execute(query)

        # Convert rows to TimecardEntry objects
        return [
            TimecardEntry(
                project_id=row.project_id,
                project_name=row.project_name,
                date=row.date,
                total_hours=row.total_hours,
            )
            for row in result.all()
        ]

    async def get_total_hours_by_project(
        self, project_id: int, start_date: date, end_date: date
    ) -> Decimal:
        """
        Get total hours worked on a project in a date range.

        Args:
            project_id: Project ID
            start_date: Range start date (inclusive)
            end_date: Range end date (inclusive)

        Returns:
            Decimal: Total hours worked (0.0 if no sessions)

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError("end_date must be after start_date")

        result = await self.session.execute(
            select(func.sum(WorkSession.duration_hours))
            .where(WorkSession.project_id == project_id)
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
        )
        total = result.scalar_one()
        return total if total is not None else Decimal("0.0")
