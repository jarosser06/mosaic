"""Integration tests for bookmark MCP tools."""

import pytest

from mosaic.models.base import EntityType, PrivacyLevel
from mosaic.schemas.bookmark import (
    AddBookmarkInput,
    DeleteBookmarkInput,
    ListBookmarksInput,
    UpdateBookmarkInput,
)
from mosaic.tools.bookmark_tools import (
    add_bookmark,
    delete_bookmark,
    list_bookmarks,
    update_bookmark,
)


@pytest.mark.asyncio
class TestBookmarkTools:
    """Test bookmark MCP tools end-to-end."""

    async def test_add_bookmark_minimal(self, mcp_client):
        """Test adding bookmark with minimal fields."""
        input_data = AddBookmarkInput(
            title="Python Docs",
            url="https://docs.python.org",
        )
        result = await add_bookmark(input_data, mcp_client)

        assert result.id is not None
        assert result.title == "Python Docs"
        assert result.url == "https://docs.python.org"
        assert result.privacy_level == PrivacyLevel.PRIVATE
        assert result.tags == []
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_add_bookmark_full(self, mcp_client):
        """Test adding bookmark with all fields."""
        input_data = AddBookmarkInput(
            title="Python AsyncIO Guide",
            url="https://docs.python.org/3/library/asyncio.html",
            description="Comprehensive async programming guide",
            entity_type=EntityType.PROJECT,
            entity_id=1,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["python", "async", "documentation"],
        )
        result = await add_bookmark(input_data, mcp_client)

        assert result.title == "Python AsyncIO Guide"
        assert result.url == "https://docs.python.org/3/library/asyncio.html"
        assert result.description == "Comprehensive async programming guide"
        assert result.entity_type == EntityType.PROJECT
        assert result.entity_id == 1
        assert result.privacy_level == PrivacyLevel.PUBLIC
        assert result.tags == ["python", "async", "documentation"]

    async def test_update_bookmark(self, mcp_client):
        """Test updating bookmark fields."""
        # Create
        input_data = AddBookmarkInput(
            title="Original",
            url="https://example.com",
        )
        created = await add_bookmark(input_data, mcp_client)

        # Update
        update_data = UpdateBookmarkInput(
            bookmark_id=created.id,
            title="Updated title",
            url="https://updated.com",
            description="New description",
            tags=["updated"],
        )
        updated = await update_bookmark(update_data, mcp_client)

        assert updated.id == created.id
        assert updated.title == "Updated title"
        assert updated.url == "https://updated.com"
        assert updated.description == "New description"
        assert updated.tags == ["updated"]

    async def test_update_bookmark_not_found(self, mcp_client):
        """Test updating non-existent bookmark raises error."""
        update_data = UpdateBookmarkInput(
            bookmark_id=99999,
            title="Should fail",
        )
        with pytest.raises(ValueError, match="not found"):
            await update_bookmark(update_data, mcp_client)

    async def test_list_bookmarks_no_filters(self, mcp_client):
        """Test listing all bookmarks."""
        # Create test bookmarks
        await add_bookmark(
            AddBookmarkInput(title="Bookmark 1", url="https://example1.com"),
            mcp_client,
        )
        await add_bookmark(
            AddBookmarkInput(title="Bookmark 2", url="https://example2.com"),
            mcp_client,
        )

        # List all
        input_data = ListBookmarksInput()
        result = await list_bookmarks(input_data, mcp_client)

        assert result.total_count >= 2
        assert len(result.bookmarks) >= 2

    async def test_list_bookmarks_filter_by_entity(self, mcp_client):
        """Test filtering bookmarks by entity."""
        # Create bookmark with entity
        await add_bookmark(
            AddBookmarkInput(
                title="Project docs",
                url="https://example.com",
                entity_type=EntityType.PROJECT,
                entity_id=42,
            ),
            mcp_client,
        )

        # Filter by entity
        input_data = ListBookmarksInput(
            entity_type=EntityType.PROJECT,
            entity_id=42,
        )
        result = await list_bookmarks(input_data, mcp_client)

        assert all(
            item.entity_type == EntityType.PROJECT and item.entity_id == 42
            for item in result.bookmarks
        )

    async def test_list_bookmarks_search_by_title(self, mcp_client):
        """Test searching bookmarks by title."""
        # Create bookmark
        await add_bookmark(
            AddBookmarkInput(title="Python Tutorial", url="https://python.org"),
            mcp_client,
        )

        # Search by title
        input_data = ListBookmarksInput(search_query="Python")
        result = await list_bookmarks(input_data, mcp_client)

        assert all("python" in item.title.lower() for item in result.bookmarks)

    async def test_list_bookmarks_search_by_url(self, mcp_client):
        """Test searching bookmarks by URL."""
        # Create bookmark
        await add_bookmark(
            AddBookmarkInput(title="Example", url="https://docs.python.org/tutorial"),
            mcp_client,
        )

        # Search by URL
        input_data = ListBookmarksInput(search_query="docs.python.org")
        result = await list_bookmarks(input_data, mcp_client)

        assert all("docs.python.org" in item.url.lower() for item in result.bookmarks)

    async def test_list_bookmarks_filter_by_tags(self, mcp_client):
        """Test filtering bookmarks by tags."""
        # Create bookmarks with tags
        await add_bookmark(
            AddBookmarkInput(
                title="Python resource",
                url="https://example.com",
                tags=["python", "tutorial"],
            ),
            mcp_client,
        )

        # Filter by tag
        input_data = ListBookmarksInput(tags=["python"])
        result = await list_bookmarks(input_data, mcp_client)

        assert all("python" in item.tags for item in result.bookmarks)

    async def test_list_bookmarks_sorting(self, mcp_client):
        """Test bookmarks are sorted by created_at descending."""
        # Create multiple bookmarks
        await add_bookmark(
            AddBookmarkInput(title="First", url="https://first.com"),
            mcp_client,
        )
        await add_bookmark(
            AddBookmarkInput(title="Second", url="https://second.com"),
            mcp_client,
        )

        # List all
        input_data = ListBookmarksInput()
        result = await list_bookmarks(input_data, mcp_client)

        # Most recent should be first
        if len(result.bookmarks) >= 2:
            assert result.bookmarks[0].created_at >= result.bookmarks[1].created_at

    async def test_delete_bookmark(self, mcp_client):
        """Test deleting bookmark."""
        # Create
        input_data = AddBookmarkInput(title="To delete", url="https://example.com")
        created = await add_bookmark(input_data, mcp_client)

        # Delete
        delete_data = DeleteBookmarkInput(bookmark_id=created.id)
        result = await delete_bookmark(delete_data, mcp_client)

        assert result.success is True
        assert "deleted successfully" in result.message

        # Verify deleted
        update_data = UpdateBookmarkInput(bookmark_id=created.id, title="Should fail")
        with pytest.raises(ValueError, match="not found"):
            await update_bookmark(update_data, mcp_client)

    async def test_delete_bookmark_not_found(self, mcp_client):
        """Test deleting non-existent bookmark raises error."""
        delete_data = DeleteBookmarkInput(bookmark_id=99999)
        with pytest.raises(ValueError, match="not found"):
            await delete_bookmark(delete_data, mcp_client)

    async def test_list_bookmarks_empty_result(self, mcp_client):
        """Test listing returns empty list when no matches."""
        input_data = ListBookmarksInput(
            entity_type=EntityType.PROJECT,
            entity_id=99999,  # Non-existent project
        )
        result = await list_bookmarks(input_data, mcp_client)

        assert result.total_count == 0
        assert result.bookmarks == []

    async def test_bookmark_long_url(self, mcp_client):
        """Test bookmark with long URL."""
        long_url = "https://example.com/" + "a" * 1900
        input_data = AddBookmarkInput(title="Long URL", url=long_url)
        result = await add_bookmark(input_data, mcp_client)

        assert result.url == long_url
        assert len(result.url) <= 2000
