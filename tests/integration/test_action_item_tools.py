"""Integration tests for action item MCP tools."""

from datetime import datetime, timezone

import pytest

from mosaic.models.base import ActionItemStatus, EntityType, PrivacyLevel
from mosaic.schemas.action_item import (
    AddActionItemInput,
    DeleteActionItemInput,
    ListActionItemsInput,
    UpdateActionItemInput,
)
from mosaic.tools.action_item_tools import (
    add_action_item,
    delete_action_item,
    list_action_items,
    update_action_item,
)


@pytest.mark.asyncio
class TestActionItemTools:
    """Test action item MCP tools end-to-end."""

    async def test_add_action_item_minimal(self, mcp_client):
        """Test adding action item with minimal fields."""
        input_data = AddActionItemInput(title="Test task")
        result = await add_action_item(input_data, mcp_client)

        assert result.id is not None
        assert result.title == "Test task"
        assert result.status == ActionItemStatus.PENDING
        assert result.privacy_level == PrivacyLevel.PRIVATE
        assert result.tags == []
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_add_action_item_full(self, mcp_client):
        """Test adding action item with all fields."""
        due_date = datetime(2026, 1, 25, 17, 0, 0, tzinfo=timezone.utc)
        input_data = AddActionItemInput(
            title="Fix login bug",
            description="Authentication fails on mobile",
            status=ActionItemStatus.IN_PROGRESS,
            due_date=due_date,
            entity_type=EntityType.PROJECT,
            entity_id=1,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["urgent", "bug"],
        )
        result = await add_action_item(input_data, mcp_client)

        assert result.title == "Fix login bug"
        assert result.description == "Authentication fails on mobile"
        assert result.status == ActionItemStatus.IN_PROGRESS
        assert result.due_date == due_date
        assert result.entity_type == EntityType.PROJECT
        assert result.entity_id == 1
        assert result.privacy_level == PrivacyLevel.INTERNAL
        assert result.tags == ["urgent", "bug"]

    async def test_update_action_item(self, mcp_client):
        """Test updating action item fields."""
        # Create
        input_data = AddActionItemInput(title="Original title")
        created = await add_action_item(input_data, mcp_client)

        # Update
        update_data = UpdateActionItemInput(
            action_item_id=created.id,
            title="Updated title",
            description="New description",
            tags=["updated"],
        )
        updated = await update_action_item(update_data, mcp_client)

        assert updated.id == created.id
        assert updated.title == "Updated title"
        assert updated.description == "New description"
        assert updated.tags == ["updated"]

    async def test_update_action_item_status_to_completed(self, mcp_client):
        """Test updating status to COMPLETED auto-sets completed_at."""
        # Create
        input_data = AddActionItemInput(title="Task to complete")
        created = await add_action_item(input_data, mcp_client)
        assert created.completed_at is None

        # Mark as completed
        update_data = UpdateActionItemInput(
            action_item_id=created.id,
            status=ActionItemStatus.COMPLETED,
        )
        updated = await update_action_item(update_data, mcp_client)

        assert updated.status == ActionItemStatus.COMPLETED
        assert updated.completed_at is not None

    async def test_update_action_item_not_found(self, mcp_client):
        """Test updating non-existent action item raises error."""
        update_data = UpdateActionItemInput(
            action_item_id=99999,
            title="Should fail",
        )
        with pytest.raises(ValueError, match="not found"):
            await update_action_item(update_data, mcp_client)

    async def test_list_action_items_no_filters(self, mcp_client):
        """Test listing all action items."""
        # Create test items
        await add_action_item(AddActionItemInput(title="Task 1"), mcp_client)
        await add_action_item(AddActionItemInput(title="Task 2"), mcp_client)

        # List all
        input_data = ListActionItemsInput()
        result = await list_action_items(input_data, mcp_client)

        assert result.total_count >= 2
        assert len(result.action_items) >= 2

    async def test_list_action_items_filter_by_status(self, mcp_client):
        """Test filtering action items by status."""
        # Create items with different statuses
        await add_action_item(
            AddActionItemInput(title="Pending", status=ActionItemStatus.PENDING),
            mcp_client,
        )
        await add_action_item(
            AddActionItemInput(title="In Progress", status=ActionItemStatus.IN_PROGRESS),
            mcp_client,
        )

        # Filter by PENDING
        input_data = ListActionItemsInput(status=ActionItemStatus.PENDING)
        result = await list_action_items(input_data, mcp_client)

        assert all(item.status == ActionItemStatus.PENDING for item in result.action_items)

    async def test_list_action_items_filter_by_entity(self, mcp_client):
        """Test filtering action items by entity."""
        # Create item with entity
        await add_action_item(
            AddActionItemInput(
                title="Project task",
                entity_type=EntityType.PROJECT,
                entity_id=42,
            ),
            mcp_client,
        )

        # Filter by entity
        input_data = ListActionItemsInput(
            entity_type=EntityType.PROJECT,
            entity_id=42,
        )
        result = await list_action_items(input_data, mcp_client)

        assert all(
            item.entity_type == EntityType.PROJECT and item.entity_id == 42
            for item in result.action_items
        )

    async def test_list_action_items_filter_overdue(self, mcp_client):
        """Test filtering overdue action items."""
        # Create overdue item
        past_date = datetime(2025, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        await add_action_item(AddActionItemInput(title="Overdue", due_date=past_date), mcp_client)

        # Filter overdue
        input_data = ListActionItemsInput(overdue_only=True)
        result = await list_action_items(input_data, mcp_client)

        assert result.total_count >= 1
        for item in result.action_items:
            if item.due_date:
                assert item.due_date < datetime.now(timezone.utc)

    async def test_list_action_items_filter_by_tags(self, mcp_client):
        """Test filtering action items by tags."""
        # Create items with tags
        await add_action_item(
            AddActionItemInput(title="Urgent task", tags=["urgent", "bug"]),
            mcp_client,
        )

        # Filter by tag
        input_data = ListActionItemsInput(tags=["urgent"])
        result = await list_action_items(input_data, mcp_client)

        assert all("urgent" in item.tags for item in result.action_items)

    async def test_list_action_items_sorting(self, mcp_client):
        """Test action items are sorted by due_date then id."""
        future1 = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        future2 = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

        await add_action_item(AddActionItemInput(title="Later", due_date=future2), mcp_client)
        await add_action_item(AddActionItemInput(title="Sooner", due_date=future1), mcp_client)

        input_data = ListActionItemsInput()
        result = await list_action_items(input_data, mcp_client)

        # Items with due dates should be sorted
        items_with_dates = [item for item in result.action_items if item.due_date is not None]
        if len(items_with_dates) >= 2:
            for i in range(len(items_with_dates) - 1):
                assert items_with_dates[i].due_date <= items_with_dates[i + 1].due_date

    async def test_delete_action_item(self, mcp_client):
        """Test deleting action item."""
        # Create
        input_data = AddActionItemInput(title="To delete")
        created = await add_action_item(input_data, mcp_client)

        # Delete
        delete_data = DeleteActionItemInput(action_item_id=created.id)
        result = await delete_action_item(delete_data, mcp_client)

        assert result.success is True
        assert "deleted successfully" in result.message

        # Verify deleted (should raise error on update)
        update_data = UpdateActionItemInput(action_item_id=created.id, title="Should fail")
        with pytest.raises(ValueError, match="not found"):
            await update_action_item(update_data, mcp_client)

    async def test_delete_action_item_not_found(self, mcp_client):
        """Test deleting non-existent action item raises error."""
        delete_data = DeleteActionItemInput(action_item_id=99999)
        with pytest.raises(ValueError, match="not found"):
            await delete_action_item(delete_data, mcp_client)

    async def test_list_action_items_empty_result(self, mcp_client):
        """Test listing returns empty list when no matches."""
        input_data = ListActionItemsInput(
            entity_type=EntityType.PROJECT,
            entity_id=99999,  # Non-existent project
        )
        result = await list_action_items(input_data, mcp_client)

        assert result.total_count == 0
        assert result.action_items == []
