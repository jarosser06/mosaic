"""Note repository for timestamped annotations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import EntityType
from ..models.note import Note
from .base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    """Repository for Note operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize note repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Note)

    async def list_by_entity(self, entity_type: EntityType, entity_id: int) -> list[Note]:
        """
        List notes for a specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            list[Note]: Notes for this entity, ordered by creation time (newest first)
        """
        result = await self.session.execute(
            select(Note)
            .where(Note.entity_type == entity_type)
            .where(Note.entity_id == entity_id)
            .order_by(Note.created_at.desc(), Note.id.desc())
        )
        return list(result.scalars().all())
