"""User repository for profile management."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User profile operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize user repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.

        Args:
            email: Email address to search for

        Returns:
            Optional[User]: User if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_current_user(self) -> Optional[User]:
        """
        Get the current user (single-user system).

        Returns:
            Optional[User]: The user if exists, None otherwise
        """
        result = await self.session.execute(select(User).limit(1))
        return result.scalar_one_or_none()
