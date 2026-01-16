"""Tests for Reminder model."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType
from src.mosaic.models.reminder import Reminder


@pytest.mark.asyncio
async def test_reminder_creation_minimal(session: AsyncSession) -> None:
    """Test creating reminder with minimal required fields."""
    reminder_time = datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)

    reminder = Reminder(
        reminder_time=reminder_time,
        message="Complete project documentation",
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert reminder.id is not None
    assert reminder.reminder_time == reminder_time
    assert reminder.message == "Complete project documentation"
    assert reminder.is_completed is False
    assert reminder.recurrence_config is None
    assert reminder.related_entity_type is None
    assert reminder.related_entity_id is None
    assert reminder.snoozed_until is None
    assert reminder.created_at is not None
    assert reminder.updated_at is not None


@pytest.mark.asyncio
async def test_reminder_creation_full(session: AsyncSession) -> None:
    """Test creating reminder with all fields populated."""
    reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
    snooze_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    recurrence = {"frequency": "daily", "interval": 1}

    reminder = Reminder(
        reminder_time=reminder_time,
        message="Daily standup meeting",
        is_completed=False,
        recurrence_config=recurrence,
        related_entity_type=EntityType.PROJECT,
        related_entity_id=42,
        snoozed_until=snooze_time,
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert reminder.message == "Daily standup meeting"
    assert reminder.is_completed is False
    assert reminder.recurrence_config == recurrence
    assert reminder.related_entity_type == EntityType.PROJECT
    assert reminder.related_entity_id == 42
    assert reminder.snoozed_until == snooze_time


@pytest.mark.asyncio
async def test_reminder_mark_completed(session: AsyncSession) -> None:
    """Test marking reminder as completed."""
    reminder = Reminder(
        reminder_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        message="Task to complete",
        is_completed=False,
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert reminder.is_completed is False

    reminder.is_completed = True
    await session.flush()
    await session.refresh(reminder)

    assert reminder.is_completed is True


@pytest.mark.asyncio
async def test_reminder_with_recurrence(session: AsyncSession) -> None:
    """Test reminder with recurrence configuration."""
    recurrence_config = {
        "frequency": "weekly",
        "interval": 1,
        "days_of_week": ["monday", "wednesday", "friday"],
    }

    reminder = Reminder(
        reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        message="Recurring team sync",
        recurrence_config=recurrence_config,
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert reminder.recurrence_config is not None
    assert reminder.recurrence_config["frequency"] == "weekly"
    assert "monday" in reminder.recurrence_config["days_of_week"]


@pytest.mark.parametrize(
    "entity_type,entity_id",
    [
        (EntityType.PERSON, 1),
        (EntityType.CLIENT, 2),
        (EntityType.PROJECT, 3),
        (EntityType.EMPLOYER, 4),
        (EntityType.WORK_SESSION, 5),
        (EntityType.MEETING, 6),
    ],
)
@pytest.mark.asyncio
async def test_reminder_entity_links(
    session: AsyncSession, entity_type: EntityType, entity_id: int
) -> None:
    """Test reminder linked to different entity types."""
    reminder = Reminder(
        reminder_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        message="Related reminder",
        related_entity_type=entity_type,
        related_entity_id=entity_id,
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert reminder.related_entity_type == entity_type
    assert reminder.related_entity_id == entity_id


@pytest.mark.asyncio
async def test_reminder_snooze(session: AsyncSession) -> None:
    """Test snoozing a reminder."""
    original_reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
    snooze_until = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)

    reminder = Reminder(
        reminder_time=original_reminder_time,
        message="Snoozable reminder",
    )
    session.add(reminder)
    await session.flush()

    reminder.snoozed_until = snooze_until
    await session.flush()
    await session.refresh(reminder)

    assert reminder.snoozed_until == snooze_until
    assert reminder.reminder_time == original_reminder_time


@pytest.mark.asyncio
async def test_reminder_due_time_indexing(session: AsyncSession) -> None:
    """Test that reminder due times are indexed and queryable."""
    reminder1 = Reminder(
        reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        message="Morning reminder",
    )
    reminder2 = Reminder(
        reminder_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        message="Afternoon reminder",
    )
    reminder3 = Reminder(
        reminder_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        message="Next day reminder",
    )
    session.add_all([reminder1, reminder2, reminder3])
    await session.flush()

    # Query by due time range
    stmt = select(Reminder).where(
        Reminder.reminder_time >= datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc),
        Reminder.reminder_time < datetime(2024, 1, 16, 0, 0, tzinfo=timezone.utc),
    )
    result = await session.execute(stmt)
    reminders = result.scalars().all()

    assert len(reminders) == 2


@pytest.mark.asyncio
async def test_reminder_active_composite_index(session: AsyncSession) -> None:
    """Test composite index on reminder_time and is_completed for active reminders."""
    reminder1 = Reminder(
        reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        message="Active reminder",
        is_completed=False,
    )
    reminder2 = Reminder(
        reminder_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        message="Completed reminder",
        is_completed=True,
    )
    reminder3 = Reminder(
        reminder_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        message="Another active",
        is_completed=False,
    )
    session.add_all([reminder1, reminder2, reminder3])
    await session.flush()

    # Query for active reminders using == operator
    stmt = select(Reminder).where(
        Reminder.is_completed == False,  # noqa: E712
        Reminder.reminder_time <= datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
    )
    result = await session.execute(stmt)
    active_reminders = result.scalars().all()

    assert len(active_reminders) == 2
    assert all(not r.is_completed for r in active_reminders)


@pytest.mark.asyncio
async def test_reminder_long_text(session: AsyncSession) -> None:
    """Test reminder with long text field."""
    long_text = "x" * 1000

    reminder = Reminder(
        reminder_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        message=long_text,
    )
    session.add(reminder)
    await session.flush()
    await session.refresh(reminder)

    assert len(reminder.message) == 1000
