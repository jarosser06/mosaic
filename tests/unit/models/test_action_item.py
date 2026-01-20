"""Unit tests for ActionItem model."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mosaic.models.action_item import ActionItem
from mosaic.models.base import ActionItemStatus, EntityType, PrivacyLevel


@pytest.mark.asyncio
class TestActionItemModel:
    """Test ActionItem model creation and validation."""

    async def test_create_action_item_minimal(self, session: AsyncSession):
        """Test creating action item with minimal required fields."""
        item = ActionItem(title="Test task")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.id is not None
        assert item.title == "Test task"
        assert item.status == ActionItemStatus.PENDING
        assert item.privacy_level == PrivacyLevel.PRIVATE
        assert item.tags == []
        assert item.description is None
        assert item.due_date is None
        assert item.completed_at is None
        assert item.entity_type is None
        assert item.entity_id is None
        assert item.created_at is not None
        assert item.updated_at is not None

    async def test_create_action_item_full(self, session: AsyncSession):
        """Test creating action item with all fields."""
        due_date = datetime(2026, 1, 25, 17, 0, 0, tzinfo=timezone.utc)
        item = ActionItem(
            title="Fix login bug",
            description="Authentication fails on mobile",
            status=ActionItemStatus.IN_PROGRESS,
            due_date=due_date,
            entity_type=EntityType.PROJECT,
            entity_id=42,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["urgent", "bug"],
        )
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.title == "Fix login bug"
        assert item.description == "Authentication fails on mobile"
        assert item.status == ActionItemStatus.IN_PROGRESS
        assert item.due_date == due_date
        assert item.entity_type == EntityType.PROJECT
        assert item.entity_id == 42
        assert item.privacy_level == PrivacyLevel.INTERNAL
        assert item.tags == ["urgent", "bug"]

    async def test_action_item_status_values(self, session: AsyncSession):
        """Test all ActionItemStatus enum values."""
        item = ActionItem(title="Test")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        item.status = ActionItemStatus.PENDING
        assert item.status == ActionItemStatus.PENDING

        item.status = ActionItemStatus.IN_PROGRESS
        assert item.status == ActionItemStatus.IN_PROGRESS

        item.status = ActionItemStatus.COMPLETED
        assert item.status == ActionItemStatus.COMPLETED

        item.status = ActionItemStatus.CANCELLED
        assert item.status == ActionItemStatus.CANCELLED

    async def test_action_item_completed_at_manual(self, session: AsyncSession):
        """Test manually setting completed_at timestamp."""
        completed_time = datetime(2026, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
        item = ActionItem(
            title="Completed task",
            status=ActionItemStatus.COMPLETED,
            completed_at=completed_time,
        )
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.completed_at == completed_time

    async def test_action_item_timezone_aware_due_date(self, session: AsyncSession):
        """Test that due_date is timezone-aware."""
        due_date = datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc)
        item = ActionItem(title="Task", due_date=due_date)
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.due_date.tzinfo is not None
        assert item.due_date.tzinfo == timezone.utc

    async def test_action_item_entity_association(self, session: AsyncSession):
        """Test entity association fields."""
        item = ActionItem(
            title="Project task",
            entity_type=EntityType.PROJECT,
            entity_id=123,
        )
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.entity_type == EntityType.PROJECT
        assert item.entity_id == 123

    async def test_action_item_privacy_levels(self, session: AsyncSession):
        """Test all privacy level values."""
        item = ActionItem(title="Test")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        item.privacy_level = PrivacyLevel.PRIVATE
        assert item.privacy_level == PrivacyLevel.PRIVATE

        item.privacy_level = PrivacyLevel.INTERNAL
        assert item.privacy_level == PrivacyLevel.INTERNAL

        item.privacy_level = PrivacyLevel.PUBLIC
        assert item.privacy_level == PrivacyLevel.PUBLIC

    async def test_action_item_tags_array(self, session: AsyncSession):
        """Test tags array handling."""
        item = ActionItem(title="Tagged task", tags=["tag1", "tag2", "tag3"])
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert len(item.tags) == 3
        assert "tag1" in item.tags
        assert "tag2" in item.tags
        assert "tag3" in item.tags

    async def test_action_item_empty_tags(self, session: AsyncSession):
        """Test empty tags default."""
        item = ActionItem(title="Untagged")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.tags == []
        assert isinstance(item.tags, list)

    async def test_action_item_title_length(self, session: AsyncSession):
        """Test title field respects max length."""
        long_title = "A" * 500
        item = ActionItem(title=long_title)
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert len(item.title) == 500
        assert item.title == long_title

    async def test_action_item_description_length(self, session: AsyncSession):
        """Test description field respects max length."""
        long_desc = "B" * 5000
        item = ActionItem(title="Test", description=long_desc)
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert len(item.description) == 5000
        assert item.description == long_desc

    async def test_action_item_no_description(self, session: AsyncSession):
        """Test action item without description."""
        item = ActionItem(title="Minimal task")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.description is None

    async def test_action_item_no_entity_association(self, session: AsyncSession):
        """Test action item without entity association."""
        item = ActionItem(title="Standalone task")
        session.add(item)
        await session.flush()
        await session.refresh(item)

        assert item.entity_type is None
        assert item.entity_id is None
