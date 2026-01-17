"""Integration tests for reminder management MCP tools.

Tests end-to-end reminder list, delete, and bulk complete operations
through MCP tool interface.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType
from src.mosaic.models.reminder import Reminder
from src.mosaic.repositories.reminder_repository import ReminderRepository
from src.mosaic.schemas.reminder_management import (
    BulkCompleteRemindersInput,
    DeleteReminderInput,
    ListRemindersInput,
    ReminderStatus,
)
from src.mosaic.tools.reminder_tools import (
    bulk_complete_reminders,
    delete_reminder,
    list_reminders,
)


class TestReminderTools:
    """Test reminder management MCP tools end-to-end."""

    @pytest.mark.asyncio
    async def test_list_reminders_empty(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test listing reminders when none exist."""
        input_data = ListRemindersInput()

        result = await list_reminders(input_data, mcp_client)

        assert result.reminders == []
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_list_reminders_all_status(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test listing all reminders regardless of status."""
        # Create reminders with different statuses
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
        snooze_time = datetime(2026, 1, 21, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Active reminder",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Completed reminder",
            is_completed=True,
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Snoozed reminder",
            is_completed=False,
            snoozed_until=snooze_time,
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()

        # List all reminders
        input_data = ListRemindersInput(status=ReminderStatus.ALL)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 3
        assert len(result.reminders) == 3

    @pytest.mark.asyncio
    async def test_list_reminders_active_only(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test listing only active (not completed, not snoozed) reminders."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
        snooze_time = datetime(2026, 1, 21, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Active reminder",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Completed reminder",
            is_completed=True,
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Snoozed reminder",
            is_completed=False,
            snoozed_until=snooze_time,
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()

        # List only active reminders
        input_data = ListRemindersInput(status=ReminderStatus.ACTIVE)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 1
        assert result.reminders[0].message == "Active reminder"
        assert result.reminders[0].completed_at is None
        assert result.reminders[0].snoozed_until is None

    @pytest.mark.asyncio
    async def test_list_reminders_completed_only(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test listing only completed reminders."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Active reminder",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Completed reminder",
            is_completed=True,
        )

        test_session.add_all([r1, r2])
        await test_session.commit()

        # List only completed reminders
        input_data = ListRemindersInput(status=ReminderStatus.COMPLETED)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 1
        assert result.reminders[0].message == "Completed reminder"
        assert result.reminders[0].completed_at is not None

    @pytest.mark.asyncio
    async def test_list_reminders_snoozed_only(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test listing only snoozed reminders."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
        snooze_time = datetime(2026, 1, 21, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Active reminder",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Snoozed reminder",
            is_completed=False,
            snoozed_until=snooze_time,
        )

        test_session.add_all([r1, r2])
        await test_session.commit()

        # List only snoozed reminders
        input_data = ListRemindersInput(status=ReminderStatus.SNOOZED)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 1
        assert result.reminders[0].message == "Snoozed reminder"
        assert result.reminders[0].snoozed_until is not None

    @pytest.mark.asyncio
    async def test_list_reminders_filter_by_entity(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test filtering reminders by entity type and ID."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Project reminder",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=1,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Client reminder",
            is_completed=False,
            related_entity_type=EntityType.CLIENT,
            related_entity_id=2,
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Another project reminder",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=3,
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()

        # Filter by entity type
        input_data = ListRemindersInput(entity_type=EntityType.PROJECT)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 2
        assert all(r.entity_type == EntityType.PROJECT for r in result.reminders)

        # Filter by entity type and ID
        input_data = ListRemindersInput(entity_type=EntityType.PROJECT, entity_id=1)
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 1
        assert result.reminders[0].message == "Project reminder"
        assert result.reminders[0].entity_id == 1

    @pytest.mark.asyncio
    async def test_list_reminders_filter_by_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test filtering reminders by tags (ANY match)."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Urgent call",
            is_completed=False,
            tags=["urgent", "call"],
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Admin task",
            is_completed=False,
            tags=["admin"],
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Urgent email",
            is_completed=False,
            tags=["urgent", "email"],
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()

        # Filter by single tag
        input_data = ListRemindersInput(tags=["urgent"])
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 2
        assert all("urgent" in r.tags for r in result.reminders)

        # Filter by multiple tags (ANY match)
        input_data = ListRemindersInput(tags=["urgent", "admin"])
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 3  # All have either "urgent" OR "admin"

    @pytest.mark.asyncio
    async def test_delete_reminder_success(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test successfully deleting a reminder."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r = Reminder(
            reminder_time=reminder_time,
            message="Test reminder",
            is_completed=False,
        )
        test_session.add(r)
        await test_session.commit()
        await test_session.refresh(r)

        reminder_id = r.id

        # Delete the reminder
        input_data = DeleteReminderInput(reminder_id=reminder_id)
        result = await delete_reminder(input_data, mcp_client)

        assert result.success is True
        assert str(reminder_id) in result.message

        # Verify it's deleted from database
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = ReminderRepository(fresh_session)
            fetched = await repo.get_by_id(reminder_id)
            assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_reminder_not_found(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test deleting a non-existent reminder raises ValueError."""
        input_data = DeleteReminderInput(reminder_id=999)

        with pytest.raises(ValueError) as exc_info:
            await delete_reminder(input_data, mcp_client)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bulk_complete_reminders_all_success(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test bulk completing multiple reminders successfully."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 1",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 2",
            is_completed=False,
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 3",
            is_completed=False,
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()
        await test_session.refresh(r1)
        await test_session.refresh(r2)
        await test_session.refresh(r3)

        # Bulk complete all three
        input_data = BulkCompleteRemindersInput(reminder_ids=[r1.id, r2.id, r3.id])
        result = await bulk_complete_reminders(input_data, mcp_client)

        assert result.completed_count == 3
        assert result.failed_count == 0
        assert result.failed_ids == []
        assert "3 reminders" in result.message

        # Verify all are completed in database
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = ReminderRepository(fresh_session)
            for reminder_id in [r1.id, r2.id, r3.id]:
                fetched = await repo.get_by_id(reminder_id)
                assert fetched is not None
                assert fetched.is_completed is True

    @pytest.mark.asyncio
    async def test_bulk_complete_reminders_partial_failure(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test bulk completing with some non-existent IDs."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 1",
            is_completed=False,
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 2",
            is_completed=False,
        )

        test_session.add_all([r1, r2])
        await test_session.commit()
        await test_session.refresh(r1)
        await test_session.refresh(r2)

        # Bulk complete with one non-existent ID
        input_data = BulkCompleteRemindersInput(reminder_ids=[r1.id, 999, r2.id])
        result = await bulk_complete_reminders(input_data, mcp_client)

        assert result.completed_count == 2
        assert result.failed_count == 1
        assert 999 in result.failed_ids
        assert "failed 1" in result.message.lower()

        # Verify existing ones are completed
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = ReminderRepository(fresh_session)
            fetched1 = await repo.get_by_id(r1.id)
            fetched2 = await repo.get_by_id(r2.id)
            assert fetched1 is not None and fetched1.is_completed is True
            assert fetched2 is not None and fetched2.is_completed is True

    @pytest.mark.asyncio
    async def test_bulk_complete_reminders_idempotent(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test bulk completing already-completed reminders is idempotent."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Reminder 1",
            is_completed=True,  # Already completed
        )

        test_session.add(r1)
        await test_session.commit()
        await test_session.refresh(r1)

        # Bulk complete again
        input_data = BulkCompleteRemindersInput(reminder_ids=[r1.id])
        result = await bulk_complete_reminders(input_data, mcp_client)

        assert result.completed_count == 1
        assert result.failed_count == 0

        # Verify still completed
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = ReminderRepository(fresh_session)
            fetched = await repo.get_by_id(r1.id)
            assert fetched is not None
            assert fetched.is_completed is True

    @pytest.mark.asyncio
    async def test_list_reminders_combined_filters(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test combining multiple filters (status + entity + tags)."""
        reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

        r1 = Reminder(
            reminder_time=reminder_time,
            message="Active project urgent",
            is_completed=False,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=1,
            tags=["urgent"],
        )
        r2 = Reminder(
            reminder_time=reminder_time,
            message="Completed project urgent",
            is_completed=True,
            related_entity_type=EntityType.PROJECT,
            related_entity_id=1,
            tags=["urgent"],
        )
        r3 = Reminder(
            reminder_time=reminder_time,
            message="Active client urgent",
            is_completed=False,
            related_entity_type=EntityType.CLIENT,
            related_entity_id=2,
            tags=["urgent"],
        )

        test_session.add_all([r1, r2, r3])
        await test_session.commit()

        # Filter: active + project + urgent tag
        input_data = ListRemindersInput(
            status=ReminderStatus.ACTIVE,
            entity_type=EntityType.PROJECT,
            tags=["urgent"],
        )
        result = await list_reminders(input_data, mcp_client)

        assert result.total_count == 1
        assert result.reminders[0].message == "Active project urgent"
