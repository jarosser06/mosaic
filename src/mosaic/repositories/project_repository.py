"""Project repository for managing projects."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.base import ProjectStatus
from ..models.project import Project
from .base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize project repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Project)

    async def get_by_id_with_relations(self, id: int) -> Optional[Project]:
        """
        Get project by ID with employer and client eagerly loaded.

        Args:
            id: Project ID

        Returns:
            Optional[Project]: Project with relations if found, None otherwise
        """
        result = await self.session.execute(
            select(Project)
            .where(Project.id == id)
            .options(joinedload(Project.employer), joinedload(Project.client))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Project]:
        """
        Find project by name.

        Args:
            name: Project name to search for

        Returns:
            Optional[Project]: Project if found, None otherwise
        """
        result = await self.session.execute(select(Project).where(Project.name == name))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Project]:
        """
        List all active projects.

        Returns:
            list[Project]: All active projects
        """
        result = await self.session.execute(
            select(Project).where(Project.status == ProjectStatus.ACTIVE)
        )
        return list(result.scalars().all())

    async def list_by_employer(self, employer_id: int) -> list[Project]:
        """
        List all projects for a specific employer.

        Args:
            employer_id: Employer ID

        Returns:
            list[Project]: All projects for this employer
        """
        result = await self.session.execute(
            select(Project).where(Project.on_behalf_of_id == employer_id)
        )
        return list(result.scalars().all())

    async def list_by_client(self, client_id: int) -> list[Project]:
        """
        List all projects for a specific client.

        Args:
            client_id: Client ID

        Returns:
            list[Project]: All projects for this client
        """
        result = await self.session.execute(select(Project).where(Project.client_id == client_id))
        return list(result.scalars().all())
