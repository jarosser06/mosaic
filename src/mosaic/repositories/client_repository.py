"""Client repository for managing clients."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import ClientStatus
from ..models.client import Client
from .base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """Repository for Client operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize client repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Client)

    async def get_by_name(self, name: str) -> Optional[Client]:
        """
        Find client by name.

        Args:
            name: Client name to search for

        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        result = await self.session.execute(select(Client).where(Client.name == name))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Client]:
        """
        List all active clients.

        Returns:
            list[Client]: All active clients
        """
        result = await self.session.execute(
            select(Client).where(Client.status == ClientStatus.ACTIVE)
        )
        return list(result.scalars().all())
