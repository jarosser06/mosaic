"""Tests for reminder management schemas (15 test cases)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import EntityType
from src.mosaic.schemas.reminder_management import (
    BulkCompleteRemindersInput,
    BulkCompleteRemindersOutput,
    DeleteReminderInput,
    DeleteReminderOutput,
    ListRemindersInput,
    ListRemindersOutput,
    ReminderItem,
    ReminderStatus,
)

# ListRemindersInput Tests


def test_list_reminders_input_defaults():
    """Test ListRemindersInput with default values."""
    schema = ListRemindersInput()

    assert schema.status == ReminderStatus.ALL
    assert schema.entity_type is None
    assert schema.entity_id is None
    assert schema.tags == []


def test_list_reminders_input_all_filters():
    """Test ListRemindersInput with all filters specified."""
    schema = ListRemindersInput(
        status=ReminderStatus.ACTIVE,
        entity_type=EntityType.PROJECT,
        entity_id=42,
        tags=["urgent", "call"],
    )

    assert schema.status == ReminderStatus.ACTIVE
    assert schema.entity_type == EntityType.PROJECT
    assert schema.entity_id == 42
    assert schema.tags == ["urgent", "call"]


def test_list_reminders_input_status_validation():
    """Test that invalid status is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ListRemindersInput(status="invalid_status")  # type: ignore
    assert "status" in str(exc_info.value).lower()


def test_list_reminders_input_entity_id_validation():
    """Test that entity_id must be positive."""
    with pytest.raises(ValidationError) as exc_info:
        ListRemindersInput(entity_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


# ReminderItem Tests


def test_reminder_item_valid():
    """Test valid ReminderItem creation."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = ReminderItem(
        id=1,
        reminder_time=reminder_time,
        message="Call client",
        entity_type=EntityType.CLIENT,
        entity_id=5,
        completed_at=None,
        snoozed_until=None,
        tags=["urgent"],
        created_at=created,
    )

    assert schema.id == 1
    assert schema.message == "Call client"
    assert schema.entity_type == EntityType.CLIENT
    assert schema.completed_at is None
    assert schema.snoozed_until is None


def test_reminder_item_rejects_naive_datetime():
    """Test that naive reminder_time is rejected."""
    naive_time = datetime(2026, 1, 20, 9, 0, 0)  # Naive

    with pytest.raises(ValidationError) as exc_info:
        ReminderItem(
            id=1,
            reminder_time=naive_time,
            message="Test",
            created_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
    assert "Datetime must be timezone-aware" in str(exc_info.value)


# ListRemindersOutput Tests


def test_list_reminders_output_empty():
    """Test ListRemindersOutput with empty list."""
    schema = ListRemindersOutput(
        reminders=[],
        total_count=0,
    )

    assert schema.reminders == []
    assert schema.total_count == 0


def test_list_reminders_output_with_items():
    """Test ListRemindersOutput with multiple items."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    items = [
        ReminderItem(
            id=1,
            reminder_time=reminder_time,
            message="Reminder 1",
            tags=[],
            created_at=created,
        ),
        ReminderItem(
            id=2,
            reminder_time=reminder_time,
            message="Reminder 2",
            tags=[],
            created_at=created,
        ),
    ]

    schema = ListRemindersOutput(
        reminders=items,
        total_count=2,
    )

    assert len(schema.reminders) == 2
    assert schema.total_count == 2


# DeleteReminderInput Tests


def test_delete_reminder_input_valid():
    """Test valid DeleteReminderInput creation."""
    schema = DeleteReminderInput(reminder_id=42)
    assert schema.reminder_id == 42


def test_delete_reminder_input_rejects_invalid_id():
    """Test that reminder_id must be > 0."""
    with pytest.raises(ValidationError) as exc_info:
        DeleteReminderInput(reminder_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


# DeleteReminderOutput Tests


def test_delete_reminder_output_valid():
    """Test valid DeleteReminderOutput creation."""
    schema = DeleteReminderOutput(
        success=True,
        message="Reminder 42 deleted successfully",
    )

    assert schema.success is True
    assert "42" in schema.message


# BulkCompleteRemindersInput Tests


def test_bulk_complete_reminders_input_valid():
    """Test valid BulkCompleteRemindersInput creation."""
    schema = BulkCompleteRemindersInput(reminder_ids=[1, 2, 3])
    assert schema.reminder_ids == [1, 2, 3]


def test_bulk_complete_reminders_input_empty_list():
    """Test that empty reminder_ids list is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        BulkCompleteRemindersInput(reminder_ids=[])
    assert "at least 1" in str(exc_info.value).lower()


# BulkCompleteRemindersOutput Tests


def test_bulk_complete_reminders_output_all_success():
    """Test BulkCompleteRemindersOutput with all successful."""
    schema = BulkCompleteRemindersOutput(
        completed_count=3,
        failed_count=0,
        failed_ids=[],
        message="Successfully completed 3 reminders",
    )

    assert schema.completed_count == 3
    assert schema.failed_count == 0
    assert schema.failed_ids == []


def test_bulk_complete_reminders_output_partial_failure():
    """Test BulkCompleteRemindersOutput with some failures."""
    schema = BulkCompleteRemindersOutput(
        completed_count=2,
        failed_count=1,
        failed_ids=[5],
        message="Completed 2 reminders, failed 1 (IDs: [5])",
    )

    assert schema.completed_count == 2
    assert schema.failed_count == 1
    assert schema.failed_ids == [5]
