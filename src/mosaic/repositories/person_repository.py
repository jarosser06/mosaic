"""Person repository with employment history management."""

from datetime import date
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.person import EmploymentHistory, Person
from .base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    """Repository for Person operations with employment history."""

    def __init__(self, session: AsyncSession):
        """
        Initialize person repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Person)

    async def get_by_id_with_employments(self, id: int) -> Optional[Person]:
        """
        Get person by ID with employment history eagerly loaded.

        Args:
            id: Person ID

        Returns:
            Optional[Person]: Person with employments if found, None otherwise
        """
        result = await self.session.execute(
            select(Person).where(Person.id == id).options(selectinload(Person.employments))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Person]:
        """
        Find person by email address.

        Args:
            email: Email address to search for

        Returns:
            Optional[Person]: Person if found, None otherwise
        """
        result = await self.session.execute(select(Person).where(Person.email == email))
        return result.scalar_one_or_none()

    async def search_by_name(self, name_pattern: str) -> list[Person]:
        """
        Search people by name pattern (case-insensitive).

        Args:
            name_pattern: Name pattern to search for (SQL LIKE pattern)

        Returns:
            list[Person]: People matching the pattern
        """
        result = await self.session.execute(
            select(Person).where(Person.full_name.ilike(f"%{name_pattern}%"))
        )
        return list(result.scalars().all())

    async def list_stakeholders(self) -> list[Person]:
        """
        List all stakeholders.

        Returns:
            list[Person]: All people marked as stakeholders
        """
        result = await self.session.execute(select(Person).where(Person.is_stakeholder.is_(True)))
        return list(result.scalars().all())

    async def add_employment(
        self,
        person_id: int,
        client_id: int,
        start_date: date,
        end_date: Optional[date] = None,
        role: Optional[str] = None,
    ) -> EmploymentHistory:
        """
        Add employment history record.

        Args:
            person_id: Person ID
            client_id: Client ID
            start_date: Employment start date
            end_date: Employment end date (None for current)
            role: Job role/title

        Returns:
            EmploymentHistory: Created employment record

        Raises:
            ValueError: If person or client does not exist
            IntegrityError: If employment record conflicts
        """
        employment = EmploymentHistory(
            person_id=person_id,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            role=role,
        )
        self.session.add(employment)
        await self.session.flush()
        await self.session.refresh(employment)
        return employment

    async def get_current_employers(self, person_id: int) -> list[EmploymentHistory]:
        """
        Get current employment records (end_date is NULL).

        Args:
            person_id: Person ID

        Returns:
            list[EmploymentHistory]: Current employment records
        """
        result = await self.session.execute(
            select(EmploymentHistory)
            .where(EmploymentHistory.person_id == person_id)
            .where(EmploymentHistory.end_date.is_(None))
        )
        return list(result.scalars().all())

    async def get_employments_at_date(
        self, person_id: int, target_date: date
    ) -> list[EmploymentHistory]:
        """
        Get employment records active at a specific date.

        Args:
            person_id: Person ID
            target_date: Date to check employment for

        Returns:
            list[EmploymentHistory]: Employment records active at target_date
        """
        result = await self.session.execute(
            select(EmploymentHistory)
            .where(EmploymentHistory.person_id == person_id)
            .where(EmploymentHistory.start_date <= target_date)
            .where(
                or_(
                    EmploymentHistory.end_date.is_(None),
                    EmploymentHistory.end_date >= target_date,
                )
            )
        )
        return list(result.scalars().all())

    async def get_employments_in_date_range(
        self, person_id: int, start_date: date, end_date: date
    ) -> list[EmploymentHistory]:
        """
        Get employment records that overlap with a date range.

        Args:
            person_id: Person ID
            start_date: Range start date
            end_date: Range end date

        Returns:
            list[EmploymentHistory]: Employment records overlapping the range

        Raises:
            ValueError: If end_date is before start_date
        """
        if end_date < start_date:
            raise ValueError("end_date must be after start_date")

        # Employment overlaps range if:
        # - Employment starts before or during range AND
        # - Employment ends after or during range (or is ongoing)
        result = await self.session.execute(
            select(EmploymentHistory)
            .where(EmploymentHistory.person_id == person_id)
            .where(EmploymentHistory.start_date <= end_date)
            .where(
                or_(
                    EmploymentHistory.end_date.is_(None),
                    EmploymentHistory.end_date >= start_date,
                )
            )
        )
        return list(result.scalars().all())
