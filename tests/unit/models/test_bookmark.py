"""Unit tests for Bookmark model."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mosaic.models.base import EntityType, PrivacyLevel
from mosaic.models.bookmark import Bookmark


@pytest.mark.asyncio
class TestBookmarkModel:
    """Test Bookmark model creation and validation."""

    async def test_create_bookmark_minimal(self, session: AsyncSession):
        """Test creating bookmark with minimal required fields."""
        bookmark = Bookmark(
            title="Python Docs",
            url="https://docs.python.org",
        )
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.id is not None
        assert bookmark.title == "Python Docs"
        assert bookmark.url == "https://docs.python.org"
        assert bookmark.privacy_level == PrivacyLevel.PRIVATE
        assert bookmark.tags == []
        assert bookmark.description is None
        assert bookmark.entity_type is None
        assert bookmark.entity_id is None
        assert bookmark.created_at is not None
        assert bookmark.updated_at is not None

    async def test_create_bookmark_full(self, session: AsyncSession):
        """Test creating bookmark with all fields."""
        bookmark = Bookmark(
            title="Python AsyncIO Guide",
            url="https://docs.python.org/3/library/asyncio.html",
            description="Comprehensive async programming guide",
            entity_type=EntityType.PROJECT,
            entity_id=42,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["python", "async", "documentation"],
        )
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.title == "Python AsyncIO Guide"
        assert bookmark.url == "https://docs.python.org/3/library/asyncio.html"
        assert bookmark.description == "Comprehensive async programming guide"
        assert bookmark.entity_type == EntityType.PROJECT
        assert bookmark.entity_id == 42
        assert bookmark.privacy_level == PrivacyLevel.PUBLIC
        assert bookmark.tags == ["python", "async", "documentation"]

    async def test_bookmark_long_url(self, session: AsyncSession):
        """Test bookmark with long URL (up to 2000 chars)."""
        base = "https://example.com/"
        long_url = base + "a" * (2000 - len(base))
        bookmark = Bookmark(title="Long URL", url=long_url)
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert len(bookmark.url) == 2000
        assert bookmark.url == long_url

    async def test_bookmark_tags_array(self, session: AsyncSession):
        """Test tags array handling."""
        bookmark = Bookmark(
            title="Tagged bookmark",
            url="https://example.com",
            tags=["tag1", "tag2", "tag3"],
        )
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert len(bookmark.tags) == 3
        assert "tag1" in bookmark.tags

    async def test_bookmark_entity_association(self, session: AsyncSession):
        """Test entity association fields."""
        bookmark = Bookmark(
            title="Project resource",
            url="https://example.com",
            entity_type=EntityType.CLIENT,
            entity_id=123,
        )
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.entity_type == EntityType.CLIENT
        assert bookmark.entity_id == 123

    async def test_bookmark_privacy_levels(self, session: AsyncSession):
        """Test all privacy level values."""
        bookmark = Bookmark(title="Test", url="https://example.com")
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        bookmark.privacy_level = PrivacyLevel.PRIVATE
        assert bookmark.privacy_level == PrivacyLevel.PRIVATE

        bookmark.privacy_level = PrivacyLevel.INTERNAL
        assert bookmark.privacy_level == PrivacyLevel.INTERNAL

        bookmark.privacy_level = PrivacyLevel.PUBLIC
        assert bookmark.privacy_level == PrivacyLevel.PUBLIC

    async def test_bookmark_description_length(self, session: AsyncSession):
        """Test description field respects max length."""
        long_desc = "B" * 2000
        bookmark = Bookmark(
            title="Test",
            url="https://example.com",
            description=long_desc,
        )
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert len(bookmark.description) == 2000

    async def test_bookmark_no_description(self, session: AsyncSession):
        """Test bookmark without description."""
        bookmark = Bookmark(title="Minimal", url="https://example.com")
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.description is None

    async def test_bookmark_no_entity_association(self, session: AsyncSession):
        """Test bookmark without entity association."""
        bookmark = Bookmark(title="Standalone", url="https://example.com")
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.entity_type is None
        assert bookmark.entity_id is None

    async def test_bookmark_empty_tags(self, session: AsyncSession):
        """Test empty tags default."""
        bookmark = Bookmark(title="Untagged", url="https://example.com")
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert bookmark.tags == []
        assert isinstance(bookmark.tags, list)

    async def test_bookmark_title_length(self, session: AsyncSession):
        """Test title field respects max length."""
        long_title = "A" * 500
        bookmark = Bookmark(title=long_title, url="https://example.com")
        session.add(bookmark)
        await session.flush()
        await session.refresh(bookmark)

        assert len(bookmark.title) == 500
