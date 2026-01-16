"""Unit tests for ReminderService with recurrence logic."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.services.reminder_service import ReminderService


class TestReminderCreation:
    """Test reminder creation and validation."""

    @pytest.mark.asyncio
    async def test_create_simple_reminder(self, session: AsyncSession):
        """Test creating a simple one-time reminder."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Test reminder",
        )

        assert reminder.id is not None
        assert reminder.message == "Test reminder"
        assert reminder.reminder_time == reminder_time
        assert reminder.is_completed is False
        assert reminder.recurrence_config is None

    @pytest.mark.asyncio
    async def test_create_reminder_with_daily_recurrence(self, session: AsyncSession):
        """Test creating a reminder with daily recurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Daily standup",
            recurrence_config={"frequency": "daily"},
        )

        assert reminder.recurrence_config == {"frequency": "daily"}

    @pytest.mark.asyncio
    async def test_create_reminder_with_weekly_recurrence(self, session: AsyncSession):
        """Test creating a reminder with weekly recurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)  # Monday

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Weekly meeting",
            recurrence_config={"frequency": "weekly", "day_of_week": 0},  # Monday
        )

        assert reminder.recurrence_config["frequency"] == "weekly"
        assert reminder.recurrence_config["day_of_week"] == 0

    @pytest.mark.asyncio
    async def test_create_reminder_with_monthly_recurrence(self, session: AsyncSession):
        """Test creating a reminder with monthly recurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Monthly report",
            recurrence_config={"frequency": "monthly", "day_of_month": 15},
        )

        assert reminder.recurrence_config["frequency"] == "monthly"
        assert reminder.recurrence_config["day_of_month"] == 15

    @pytest.mark.asyncio
    async def test_create_reminder_with_related_entity(self, session: AsyncSession):
        """Test creating a reminder linked to an entity."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Follow up on project",
            related_entity_type="project",
            related_entity_id=123,
        )

        assert reminder.related_entity_type == "project"
        assert reminder.related_entity_id == 123


class TestRecurrenceValidation:
    """Test validation of recurrence configurations."""

    @pytest.mark.asyncio
    async def test_recurrence_missing_frequency_raises_error(self, session: AsyncSession):
        """Test recurrence config without frequency raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="must contain 'frequency' key"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={},
            )

    @pytest.mark.asyncio
    async def test_recurrence_invalid_frequency_raises_error(self, session: AsyncSession):
        """Test invalid frequency value raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="frequency must be one of"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={"frequency": "yearly"},
            )

    @pytest.mark.asyncio
    async def test_weekly_recurrence_missing_day_of_week_raises_error(self, session: AsyncSession):
        """Test weekly recurrence without day_of_week raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="weekly recurrence requires 'day_of_week'"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={"frequency": "weekly"},
            )

    @pytest.mark.asyncio
    async def test_weekly_recurrence_invalid_day_of_week_raises_error(self, session: AsyncSession):
        """Test weekly recurrence with invalid day_of_week raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="day_of_week must be an integer 0-6"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={"frequency": "weekly", "day_of_week": 7},
            )

    @pytest.mark.asyncio
    async def test_monthly_recurrence_missing_day_of_month_raises_error(
        self, session: AsyncSession
    ):
        """Test monthly recurrence without day_of_month raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="monthly recurrence requires 'day_of_month'"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={"frequency": "monthly"},
            )

    @pytest.mark.asyncio
    async def test_monthly_recurrence_invalid_day_of_month_raises_error(
        self, session: AsyncSession
    ):
        """Test monthly recurrence with invalid day_of_month raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="day_of_month must be an integer 1-31"):
            await service.create_reminder(
                reminder_time=reminder_time,
                message="Test",
                recurrence_config={"frequency": "monthly", "day_of_month": 32},
            )


class TestReminderCompletion:
    """Test completing reminders and generating next occurrences."""

    @pytest.mark.asyncio
    async def test_complete_simple_reminder(self, session: AsyncSession):
        """Test completing a non-recurring reminder."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Test")
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert reminder.is_completed is True
        assert next_reminder is None

    @pytest.mark.asyncio
    async def test_complete_daily_recurring_reminder(self, session: AsyncSession):
        """Test completing a daily recurring reminder creates next occurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Daily reminder",
            recurrence_config={"frequency": "daily"},
        )
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert reminder.is_completed is True
        assert next_reminder is not None
        assert next_reminder.message == "Daily reminder"
        assert next_reminder.is_completed is False
        assert next_reminder.reminder_time == reminder_time + timedelta(days=1)

    @pytest.mark.asyncio
    async def test_complete_weekly_recurring_reminder(self, session: AsyncSession):
        """Test completing a weekly recurring reminder creates next occurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)  # Monday

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Weekly reminder",
            recurrence_config={"frequency": "weekly", "day_of_week": 0},
        )
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert next_reminder is not None
        assert next_reminder.reminder_time == reminder_time + timedelta(weeks=1)

    @pytest.mark.asyncio
    async def test_complete_monthly_recurring_reminder(self, session: AsyncSession):
        """Test completing a monthly recurring reminder creates next occurrence."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Monthly reminder",
            recurrence_config={"frequency": "monthly", "day_of_month": 15},
        )
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert next_reminder is not None
        assert next_reminder.reminder_time.day == 15
        assert next_reminder.reminder_time.month == 2  # February

    @pytest.mark.asyncio
    async def test_complete_reminder_not_found_raises_error(self, session: AsyncSession):
        """Test completing non-existent reminder raises error."""
        service = ReminderService(session)

        with pytest.raises(ValueError, match="Reminder with ID 999 not found"):
            await service.complete_reminder(999)

    @pytest.mark.asyncio
    async def test_complete_reminder_clears_snooze(self, session: AsyncSession):
        """Test completing a snoozed reminder clears the snooze."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Test")
        await session.commit()

        # Snooze it
        snooze_until = reminder_time + timedelta(hours=1)
        await service.snooze_reminder(reminder.id, snooze_until)
        await session.commit()

        # Complete it
        await service.complete_reminder(reminder.id)
        await session.commit()

        assert reminder.snoozed_until is None


class TestReminderSnoozing:
    """Test snoozing reminders."""

    @pytest.mark.asyncio
    async def test_snooze_reminder(self, session: AsyncSession):
        """Test snoozing a reminder."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Test")
        await session.commit()

        snooze_until = reminder_time + timedelta(hours=1)
        updated = await service.snooze_reminder(reminder.id, snooze_until)
        await session.commit()

        assert updated.snoozed_until == snooze_until

    @pytest.mark.asyncio
    async def test_snooze_reminder_past_time_raises_error(self, session: AsyncSession):
        """Test snoozing to past time raises error."""
        service = ReminderService(session)
        reminder_time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Test")
        await session.commit()

        past_time = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="snooze_until must be in the future"):
            await service.snooze_reminder(reminder.id, past_time)

    @pytest.mark.asyncio
    async def test_snooze_reminder_not_found_raises_error(self, session: AsyncSession):
        """Test snoozing non-existent reminder raises error."""
        service = ReminderService(session)
        snooze_until = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(ValueError, match="Reminder with ID 999 not found"):
            await service.snooze_reminder(999, snooze_until)


class TestCheckDueReminders:
    """Test checking for due reminders."""

    @pytest.mark.asyncio
    async def test_check_due_reminders_returns_due_reminder(self, session: AsyncSession):
        """Test check_due_reminders returns reminders that are due."""
        service = ReminderService(session)
        # Create reminder due 1 hour ago
        reminder_time = datetime.now(timezone.utc) - timedelta(hours=1)

        await service.create_reminder(reminder_time=reminder_time, message="Overdue")
        await session.commit()

        due_reminders = await service.check_due_reminders()

        assert len(due_reminders) == 1
        assert due_reminders[0].message == "Overdue"

    @pytest.mark.asyncio
    async def test_check_due_reminders_excludes_future_reminders(self, session: AsyncSession):
        """Test check_due_reminders excludes future reminders."""
        service = ReminderService(session)
        # Create reminder due in 1 hour
        reminder_time = datetime.now(timezone.utc) + timedelta(hours=1)

        await service.create_reminder(reminder_time=reminder_time, message="Future")
        await session.commit()

        due_reminders = await service.check_due_reminders()

        assert len(due_reminders) == 0

    @pytest.mark.asyncio
    async def test_check_due_reminders_excludes_completed(self, session: AsyncSession):
        """Test check_due_reminders excludes completed reminders."""
        service = ReminderService(session)
        reminder_time = datetime.now(timezone.utc) - timedelta(hours=1)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Completed")
        await session.commit()

        # Complete it
        await service.complete_reminder(reminder.id)
        await session.commit()

        due_reminders = await service.check_due_reminders()

        assert len(due_reminders) == 0

    @pytest.mark.asyncio
    async def test_check_due_reminders_excludes_snoozed(self, session: AsyncSession):
        """Test check_due_reminders excludes snoozed reminders."""
        service = ReminderService(session)
        reminder_time = datetime.now(timezone.utc) - timedelta(hours=1)

        reminder = await service.create_reminder(reminder_time=reminder_time, message="Snoozed")
        await session.commit()

        # Snooze it to future
        snooze_until = datetime.now(timezone.utc) + timedelta(hours=1)
        await service.snooze_reminder(reminder.id, snooze_until)
        await session.commit()

        due_reminders = await service.check_due_reminders()

        assert len(due_reminders) == 0


class TestRecurrenceCalculation:
    """Test recurrence date calculation edge cases."""

    @pytest.mark.asyncio
    async def test_monthly_recurrence_handles_short_month(self, session: AsyncSession):
        """Test monthly recurrence handles month end overflow (Jan 31 -> Feb 28)."""
        service = ReminderService(session)
        # January 31st
        reminder_time = datetime(2024, 1, 31, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Month end",
            recurrence_config={"frequency": "monthly", "day_of_month": 31},
        )
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert next_reminder is not None
        # February 2024 has 29 days (leap year)
        assert next_reminder.reminder_time.day == 29
        assert next_reminder.reminder_time.month == 2

    @pytest.mark.asyncio
    async def test_monthly_recurrence_handles_year_rollover(self, session: AsyncSession):
        """Test monthly recurrence handles December to January."""
        service = ReminderService(session)
        # December 15th
        reminder_time = datetime(2024, 12, 15, 9, 0, 0, tzinfo=timezone.utc)

        reminder = await service.create_reminder(
            reminder_time=reminder_time,
            message="Year rollover",
            recurrence_config={"frequency": "monthly", "day_of_month": 15},
        )
        await session.commit()

        next_reminder = await service.complete_reminder(reminder.id)
        await session.commit()

        assert next_reminder is not None
        assert next_reminder.reminder_time.year == 2025
        assert next_reminder.reminder_time.month == 1
        assert next_reminder.reminder_time.day == 15
