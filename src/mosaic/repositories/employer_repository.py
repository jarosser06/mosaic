"""Employer repository for managing employers."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.employer import Employer
from .base import BaseRepository


class EmployerRepository(BaseRepository[Employer]):
    """Repository for Employer operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize employer repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Employer)

    async def get_current_employer(self) -> Optional[Employer]:
        """
        Get the current employer (is_current=True).

        Returns:
            Optional[Employer]: Current employer if found, None otherwise
        """
        result = await self.session.execute(select(Employer).where(Employer.is_current.is_(True)))
        return result.scalar_one_or_none()

    async def get_self_employer(self) -> Optional[Employer]:
        """
        Get the self employer (is_self=True).

        Returns:
            Optional[Employer]: Self employer if found, None otherwise
        """
        result = await self.session.execute(select(Employer).where(Employer.is_self.is_(True)))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Employer]:
        """
        Find employer by name.

        Args:
            name: Employer name to search for

        Returns:
            Optional[Employer]: Employer if found, None otherwise
        """
        result = await self.session.execute(select(Employer).where(Employer.name == name))
        return result.scalar_one_or_none()
