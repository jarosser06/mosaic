"""Tests for reminder schemas (10 test cases)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import EntityType
from src.mosaic.schemas.reminder import (
    AddReminderInput,
    AddReminderOutput,
    CompleteReminderInput,
    SnoozeReminderInput,
    SnoozeReminderOutput,
)


def test_add_reminder_input_valid():
    """Test valid AddReminderInput creation."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

    schema = AddReminderInput(
        reminder_time=reminder_time,
        message="Call client about project status",
        entity_type=EntityType.PROJECT,
        entity_id=42,
        tags=["urgent", "call"],
    )

    assert schema.reminder_time == reminder_time
    assert schema.message == "Call client about project status"
    assert schema.entity_type == EntityType.PROJECT
    assert schema.entity_id == 42
    assert schema.tags == ["urgent", "call"]


def test_add_reminder_input_rejects_naive_datetime():
    """Test that naive reminder_time is rejected."""
    naive_time = datetime(2026, 1, 20, 9, 0, 0)  # Naive

    with pytest.raises(ValidationError) as exc_info:
        AddReminderInput(
            reminder_time=naive_time,
            message="Reminder",
        )
    assert "Datetime must be timezone-aware" in str(exc_info.value)


def test_add_reminder_input_message_min_length():
    """Test that empty message is rejected."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        AddReminderInput(reminder_time=reminder_time, message="")
    assert "at least 1 character" in str(exc_info.value).lower()


def test_add_reminder_input_message_max_length():
    """Test that message exceeding max_length is rejected."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    long_message = "x" * 1001  # Exceeds 1000 max

    with pytest.raises(ValidationError) as exc_info:
        AddReminderInput(reminder_time=reminder_time, message=long_message)
    assert "at most 1000 characters" in str(exc_info.value).lower()


def test_add_reminder_input_optional_entity():
    """Test AddReminderInput without entity attachment."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

    schema = AddReminderInput(
        reminder_time=reminder_time,
        message="Submit timesheet",
    )

    assert schema.entity_type is None
    assert schema.entity_id is None
    assert schema.tags == []


def test_add_reminder_output_valid():
    """Test valid AddReminderOutput creation."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = AddReminderOutput(
        id=1,
        reminder_time=reminder_time,
        message="Call client",
        entity_type=EntityType.CLIENT,
        entity_id=5,
        completed_at=None,
        snoozed_until=None,
        tags=["urgent"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.completed_at is None
    assert schema.snoozed_until is None


def test_complete_reminder_input_valid():
    """Test valid CompleteReminderInput creation."""
    schema = CompleteReminderInput(reminder_id=42)
    assert schema.reminder_id == 42


def test_complete_reminder_input_rejects_invalid_id():
    """Test that reminder_id must be > 0."""
    with pytest.raises(ValidationError) as exc_info:
        CompleteReminderInput(reminder_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


def test_snooze_reminder_input_valid():
    """Test valid SnoozeReminderInput creation."""
    snooze_time = datetime(2026, 1, 20, 14, 0, 0, tzinfo=timezone.utc)

    schema = SnoozeReminderInput(
        reminder_id=42,
        snooze_until=snooze_time,
    )

    assert schema.reminder_id == 42
    assert schema.snooze_until == snooze_time


def test_snooze_reminder_output_valid():
    """Test valid SnoozeReminderOutput creation."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    snoozed_time = datetime(2026, 1, 20, 14, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)

    schema = SnoozeReminderOutput(
        id=1,
        reminder_time=reminder_time,
        message="Call client",
        entity_type=None,
        entity_id=None,
        completed_at=None,
        snoozed_until=snoozed_time,
        tags=["urgent"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.snoozed_until == snoozed_time
    assert schema.completed_at is None
