"""MCP tools for action item management operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import Context
from sqlalchemy import String, cast, select
from sqlalchemy.dialects.postgresql import ARRAY

from ..models.action_item import ActionItem
from ..models.base import ActionItemStatus
from ..repositories.action_item_repository import ActionItemRepository
from ..schemas.action_item import (
    ActionItemItem,
    AddActionItemInput,
    AddActionItemOutput,
    DeleteActionItemInput,
    DeleteActionItemOutput,
    ListActionItemsInput,
    ListActionItemsOutput,
    UpdateActionItemInput,
    UpdateActionItemOutput,
)
from ..server import AppContext, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def add_action_item(
    input: AddActionItemInput, ctx: Context[Any, AppContext, AddActionItemInput]
) -> AddActionItemOutput:
    """
    Add a new action item for task management.

    Create a new action item with status tracking, optional due dates,
    and entity associations. Supports organizing with tags and privacy levels.

    Args:
        input: Action item details (title, description, status, due_date, etc.)
        ctx: MCP context with app resources

    Returns:
        AddActionItemOutput: Created action item with ID and timestamps

    Raises:
        ValueError: If validation fails
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = ActionItemRepository(session)

        # Create action item
        action_item = await repo.create(
            title=input.title,
            description=input.description,
            status=input.status,
            due_date=input.due_date,
            entity_type=input.entity_type,
            entity_id=input.entity_id,
            privacy_level=input.privacy_level,
            tags=input.tags,
        )

        await session.commit()

        return AddActionItemOutput(
            id=action_item.id,
            title=action_item.title,
            description=action_item.description,
            status=action_item.status,
            due_date=action_item.due_date,
            completed_at=action_item.completed_at,
            entity_type=action_item.entity_type,
            entity_id=action_item.entity_id,
            privacy_level=action_item.privacy_level,
            tags=action_item.tags,
            created_at=action_item.created_at,
            updated_at=action_item.updated_at,
        )


@mcp.tool()
async def update_action_item(
    input: UpdateActionItemInput, ctx: Context[Any, AppContext, UpdateActionItemInput]
) -> UpdateActionItemOutput:
    """
    Update an existing action item.

    Modify any field of an action item. When changing status to COMPLETED,
    automatically sets the completed_at timestamp.

    Args:
        input: Action item ID and fields to update
        ctx: MCP context with app resources

    Returns:
        UpdateActionItemOutput: Updated action item

    Raises:
        ValueError: If action item not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = ActionItemRepository(session)

        # Build update data
        update_data: dict[str, Any] = {}
        if input.title is not None:
            update_data["title"] = input.title
        if input.description is not None:
            update_data["description"] = input.description
        if input.status is not None:
            update_data["status"] = input.status
            # Auto-set completed_at when changing to COMPLETED
            if input.status == ActionItemStatus.COMPLETED:
                update_data["completed_at"] = datetime.now(timezone.utc)
        if input.due_date is not None:
            update_data["due_date"] = input.due_date
        if input.entity_type is not None:
            update_data["entity_type"] = input.entity_type
        if input.entity_id is not None:
            update_data["entity_id"] = input.entity_id
        if input.privacy_level is not None:
            update_data["privacy_level"] = input.privacy_level
        if input.tags is not None:
            update_data["tags"] = input.tags

        # Update action item
        action_item = await repo.update(input.action_item_id, **update_data)

        if action_item is None:
            raise ValueError(f"Action item with ID {input.action_item_id} not found")

        await session.commit()

        return UpdateActionItemOutput(
            id=action_item.id,
            title=action_item.title,
            description=action_item.description,
            status=action_item.status,
            due_date=action_item.due_date,
            completed_at=action_item.completed_at,
            entity_type=action_item.entity_type,
            entity_id=action_item.entity_id,
            privacy_level=action_item.privacy_level,
            tags=action_item.tags,
            created_at=action_item.created_at,
            updated_at=action_item.updated_at,
        )


@mcp.tool()
async def list_action_items(
    input: ListActionItemsInput, ctx: Context[Any, AppContext, ListActionItemsInput]
) -> ListActionItemsOutput:
    """
    List and filter action items.

    Retrieve action items based on status, entity attachments, overdue status,
    and tags. Useful for managing tasks, finding overdue items, or viewing
    items by project/client/etc.

    Args:
        input: Filter criteria (status, entity_type, entity_id, overdue_only, tags)
        ctx: MCP context with app resources

    Returns:
        ListActionItemsOutput: List of matching action items with total count

    Raises:
        None (returns empty list if no matches)
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            # Start with base query
            query = select(ActionItem)

            # Apply status filter
            if input.status is not None:
                query = query.where(ActionItem.status == input.status)

            # Apply entity filters
            if input.entity_type is not None:
                query = query.where(ActionItem.entity_type == input.entity_type)
            if input.entity_id is not None:
                query = query.where(ActionItem.entity_id == input.entity_id)

            # Apply overdue filter
            if input.overdue_only:
                current_time = datetime.now(timezone.utc)
                query = query.where(
                    ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS])
                )
                query = query.where(ActionItem.due_date < current_time)

            # Apply tag filter (action items with ANY of the specified tags)
            if input.tags:
                # Use PostgreSQL array overlap operator (&&)
                query = query.where(ActionItem.tags.op("&&")(cast(input.tags, ARRAY(String))))

            # Apply sorting
            query = query.order_by(ActionItem.due_date.asc().nullslast(), ActionItem.id.asc())

            # Execute query
            result = await session.execute(query)
            action_items = list(result.scalars().all())

            # Convert to output format
            items = [
                ActionItemItem(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    status=item.status,
                    due_date=item.due_date,
                    completed_at=item.completed_at,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    privacy_level=item.privacy_level,
                    tags=item.tags,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in action_items
            ]

            return ListActionItemsOutput(action_items=items, total_count=len(items))

        except Exception as e:
            logger.error(f"Error listing action items: {e}")
            return ListActionItemsOutput(action_items=[], total_count=0)


@mcp.tool()
async def delete_action_item(
    input: DeleteActionItemInput, ctx: Context[Any, AppContext, DeleteActionItemInput]
) -> DeleteActionItemOutput:
    """
    Delete an action item.

    Permanently remove an action item from the system. This action cannot be undone.

    Args:
        input: Action item ID to delete
        ctx: MCP context with app resources

    Returns:
        DeleteActionItemOutput: Confirmation of deletion

    Raises:
        ValueError: If action item not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = ActionItemRepository(session)

        # Delete action item
        success = await repo.delete(input.action_item_id)

        if not success:
            raise ValueError(f"Action item with ID {input.action_item_id} not found")

        await session.commit()

        return DeleteActionItemOutput(
            success=True, message=f"Action item {input.action_item_id} deleted successfully"
        )
