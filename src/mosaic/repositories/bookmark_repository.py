"""Bookmark repository for resource link management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import EntityType
from ..models.bookmark import Bookmark
from .base import BaseRepository


class BookmarkRepository(BaseRepository[Bookmark]):
    """Repository for Bookmark operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize bookmark repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Bookmark)

    async def list_by_entity(self, entity_type: EntityType, entity_id: int) -> list[Bookmark]:
        """
        List bookmarks for a specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            list[Bookmark]: Bookmarks for this entity
        """
        result = await self.session.execute(
            select(Bookmark)
            .where(Bookmark.entity_type == entity_type)
            .where(Bookmark.entity_id == entity_id)
            .order_by(Bookmark.created_at.desc())
        )
        return list(result.scalars().all())

    async def search_by_title(self, query: str) -> list[Bookmark]:
        """
        Search bookmarks by title (case-insensitive).

        Args:
            query: Search query for title

        Returns:
            list[Bookmark]: Bookmarks matching the title query
        """
        result = await self.session.execute(
            select(Bookmark)
            .where(Bookmark.title.ilike(f"%{query}%"))
            .order_by(Bookmark.created_at.desc())
        )
        return list(result.scalars().all())

    async def search_by_url(self, url_fragment: str) -> list[Bookmark]:
        """
        Search bookmarks by URL fragment (case-insensitive).

        Args:
            url_fragment: URL fragment to search for

        Returns:
            list[Bookmark]: Bookmarks matching the URL fragment
        """
        result = await self.session.execute(
            select(Bookmark)
            .where(Bookmark.url.ilike(f"%{url_fragment}%"))
            .order_by(Bookmark.created_at.desc())
        )
        return list(result.scalars().all())
