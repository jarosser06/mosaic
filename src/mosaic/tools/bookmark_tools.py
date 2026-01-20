"""MCP tools for bookmark management operations."""

import logging
from typing import Any

from mcp.server.fastmcp import Context
from sqlalchemy import String, cast, or_, select
from sqlalchemy.dialects.postgresql import ARRAY

from ..models.bookmark import Bookmark
from ..repositories.bookmark_repository import BookmarkRepository
from ..schemas.bookmark import (
    AddBookmarkInput,
    AddBookmarkOutput,
    BookmarkItem,
    DeleteBookmarkInput,
    DeleteBookmarkOutput,
    ListBookmarksInput,
    ListBookmarksOutput,
    UpdateBookmarkInput,
    UpdateBookmarkOutput,
)
from ..server import AppContext, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def add_bookmark(
    input: AddBookmarkInput, ctx: Context[Any, AppContext, AddBookmarkInput]
) -> AddBookmarkOutput:
    """
    Add a new bookmark for resource link management.

    Create a new bookmark with URL, title, description, and optional entity
    associations. Supports organizing with tags and privacy levels.

    Args:
        input: Bookmark details (title, url, description, entity, etc.)
        ctx: MCP context with app resources

    Returns:
        AddBookmarkOutput: Created bookmark with ID and timestamps

    Raises:
        ValueError: If validation fails
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = BookmarkRepository(session)

        # Create bookmark
        bookmark = await repo.create(
            title=input.title,
            url=input.url,
            description=input.description,
            entity_type=input.entity_type,
            entity_id=input.entity_id,
            privacy_level=input.privacy_level,
            tags=input.tags,
        )

        await session.commit()

        return AddBookmarkOutput(
            id=bookmark.id,
            title=bookmark.title,
            url=bookmark.url,
            description=bookmark.description,
            entity_type=bookmark.entity_type,
            entity_id=bookmark.entity_id,
            privacy_level=bookmark.privacy_level,
            tags=bookmark.tags,
            created_at=bookmark.created_at,
            updated_at=bookmark.updated_at,
        )


@mcp.tool()
async def update_bookmark(
    input: UpdateBookmarkInput, ctx: Context[Any, AppContext, UpdateBookmarkInput]
) -> UpdateBookmarkOutput:
    """
    Update an existing bookmark.

    Modify any field of a bookmark including title, URL, description,
    entity associations, privacy level, or tags.

    Args:
        input: Bookmark ID and fields to update
        ctx: MCP context with app resources

    Returns:
        UpdateBookmarkOutput: Updated bookmark

    Raises:
        ValueError: If bookmark not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = BookmarkRepository(session)

        # Build update data
        update_data: dict[str, Any] = {}
        if input.title is not None:
            update_data["title"] = input.title
        if input.url is not None:
            update_data["url"] = input.url
        if input.description is not None:
            update_data["description"] = input.description
        if input.entity_type is not None:
            update_data["entity_type"] = input.entity_type
        if input.entity_id is not None:
            update_data["entity_id"] = input.entity_id
        if input.privacy_level is not None:
            update_data["privacy_level"] = input.privacy_level
        if input.tags is not None:
            update_data["tags"] = input.tags

        # Update bookmark
        bookmark = await repo.update(input.bookmark_id, **update_data)

        if bookmark is None:
            raise ValueError(f"Bookmark with ID {input.bookmark_id} not found")

        await session.commit()

        return UpdateBookmarkOutput(
            id=bookmark.id,
            title=bookmark.title,
            url=bookmark.url,
            description=bookmark.description,
            entity_type=bookmark.entity_type,
            entity_id=bookmark.entity_id,
            privacy_level=bookmark.privacy_level,
            tags=bookmark.tags,
            created_at=bookmark.created_at,
            updated_at=bookmark.updated_at,
        )


@mcp.tool()
async def list_bookmarks(
    input: ListBookmarksInput, ctx: Context[Any, AppContext, ListBookmarksInput]
) -> ListBookmarksOutput:
    """
    List and filter bookmarks.

    Retrieve bookmarks based on entity attachments, search query (title/URL),
    and tags. Useful for finding documentation links, organizing resources
    by project/client, or searching bookmarks.

    Args:
        input: Filter criteria (entity_type, entity_id, search_query, tags)
        ctx: MCP context with app resources

    Returns:
        ListBookmarksOutput: List of matching bookmarks with total count

    Raises:
        None (returns empty list if no matches)
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            # Start with base query
            query = select(Bookmark)

            # Apply entity filters
            if input.entity_type is not None:
                query = query.where(Bookmark.entity_type == input.entity_type)
            if input.entity_id is not None:
                query = query.where(Bookmark.entity_id == input.entity_id)

            # Apply search query (search in title or URL)
            if input.search_query:
                search_pattern = f"%{input.search_query}%"
                query = query.where(
                    or_(Bookmark.title.ilike(search_pattern), Bookmark.url.ilike(search_pattern))
                )

            # Apply tag filter (bookmarks with ANY of the specified tags)
            if input.tags:
                # Use PostgreSQL array overlap operator (&&)
                query = query.where(Bookmark.tags.op("&&")(cast(input.tags, ARRAY(String))))

            # Apply sorting (most recent first)
            query = query.order_by(Bookmark.created_at.desc())

            # Execute query
            result = await session.execute(query)
            bookmarks = list(result.scalars().all())

            # Convert to output format
            items = [
                BookmarkItem(
                    id=item.id,
                    title=item.title,
                    url=item.url,
                    description=item.description,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    privacy_level=item.privacy_level,
                    tags=item.tags,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in bookmarks
            ]

            return ListBookmarksOutput(bookmarks=items, total_count=len(items))

        except Exception as e:
            logger.error(f"Error listing bookmarks: {e}")
            return ListBookmarksOutput(bookmarks=[], total_count=0)


@mcp.tool()
async def delete_bookmark(
    input: DeleteBookmarkInput, ctx: Context[Any, AppContext, DeleteBookmarkInput]
) -> DeleteBookmarkOutput:
    """
    Delete a bookmark.

    Permanently remove a bookmark from the system. This action cannot be undone.

    Args:
        input: Bookmark ID to delete
        ctx: MCP context with app resources

    Returns:
        DeleteBookmarkOutput: Confirmation of deletion

    Raises:
        ValueError: If bookmark not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = BookmarkRepository(session)

        # Delete bookmark
        success = await repo.delete(input.bookmark_id)

        if not success:
            raise ValueError(f"Bookmark with ID {input.bookmark_id} not found")

        await session.commit()

        return DeleteBookmarkOutput(
            success=True, message=f"Bookmark {input.bookmark_id} deleted successfully"
        )
