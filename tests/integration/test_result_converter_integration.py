"""Integration tests for ResultConverter with real database models.

This test suite validates that ResultConverter correctly handles real SQLAlchemy
model instances retrieved from the database, ensuring schema alignment.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType
from src.mosaic.models.reminder import Reminder
from src.mosaic.schemas.query import ReminderResult
from src.mosaic.services.result_converter import ResultConverter


class TestResultConverterIntegration:
    """Integration tests for ResultConverter with real database models."""

    @pytest.mark.asyncio
    async def test_convert_reminder_from_database(
        self,
        test_session: AsyncSession,
    ):
        """Test converting a real Reminder model from the database.

        This test creates a Reminder in the test database with is_completed=False,
        retrieves it (getting a real SQLAlchemy model instance), uses ResultConverter
        to convert it, and validates that the result has is_completed field
        (not completed_at).
        """
        # Create a reminder in the database
        reminder_time = datetime.now(timezone.utc) + timedelta(hours=1)
        reminder = Reminder(
            reminder_time=reminder_time,
            message="Test reminder from database",
            is_completed=False,
            tags=["test", "integration"],
            related_entity_type=EntityType.PROJECT,
            related_entity_id=1,
        )

        test_session.add(reminder)
        await test_session.commit()
        await test_session.refresh(reminder)

        # Verify the reminder was created correctly
        assert reminder.id is not None
        assert reminder.is_completed is False
        assert hasattr(reminder, "is_completed")
        assert not hasattr(reminder, "completed_at")

        # Convert the real database model using ResultConverter
        converter = ResultConverter()
        raw_results = {"reminders": [reminder]}
        results = converter.convert_results(raw_results)

        # Validate the conversion
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, ReminderResult)
        assert result.id == reminder.id
        assert result.reminder_time == reminder_time
        assert result.message == "Test reminder from database"
        assert result.entity_type_attached == EntityType.PROJECT
        assert result.entity_id_attached == 1
        assert result.tags == ["test", "integration"]

        # Verify is_completed field is correctly mapped
        assert hasattr(result, "is_completed")
        assert result.is_completed is False

    @pytest.mark.asyncio
    async def test_convert_completed_reminder_from_database(
        self,
        test_session: AsyncSession,
    ):
        """Test converting a completed reminder from the database.

        Validates that completed reminders are correctly converted with
        is_completed=True.
        """
        # Create a completed reminder
        reminder_time = datetime.now(timezone.utc) - timedelta(hours=1)
        reminder = Reminder(
            reminder_time=reminder_time,
            message="Completed reminder",
            is_completed=True,
            tags=["completed"],
        )

        test_session.add(reminder)
        await test_session.commit()
        await test_session.refresh(reminder)

        # Verify the reminder was created correctly
        assert reminder.is_completed is True

        # Convert using ResultConverter
        converter = ResultConverter()
        result = converter._convert_reminder(reminder)

        # Validate the conversion
        assert result.id == reminder.id
        assert result.message == "Completed reminder"

        # Verify is_completed field is correctly mapped for completed reminder
        assert hasattr(result, "is_completed")
        assert result.is_completed is True

    @pytest.mark.asyncio
    async def test_convert_snoozed_reminder_from_database(
        self,
        test_session: AsyncSession,
    ):
        """Test converting a snoozed reminder from the database.

        Validates that snoozed reminders retain both is_completed and
        snoozed_until fields.
        """
        # Create a snoozed reminder
        reminder_time = datetime.now(timezone.utc) - timedelta(hours=1)
        snoozed_until = datetime.now(timezone.utc) + timedelta(hours=2)
        reminder = Reminder(
            reminder_time=reminder_time,
            message="Snoozed reminder",
            is_completed=False,
            snoozed_until=snoozed_until,
            tags=["snoozed"],
        )

        test_session.add(reminder)
        await test_session.commit()
        await test_session.refresh(reminder)

        # Verify the reminder was created correctly
        assert reminder.is_completed is False
        assert reminder.snoozed_until == snoozed_until

        # Convert using ResultConverter
        converter = ResultConverter()
        result = converter._convert_reminder(reminder)

        # Validate the conversion
        assert result.id == reminder.id
        assert result.message == "Snoozed reminder"
        assert result.snoozed_until == snoozed_until

        # Verify is_completed field is correctly mapped for snoozed reminder
        assert hasattr(result, "is_completed")
        assert result.is_completed is False

    @pytest.mark.asyncio
    async def test_convert_multiple_reminders_from_database(
        self,
        test_session: AsyncSession,
    ):
        """Test converting multiple reminders from the database.

        Validates bulk conversion of mixed completed/uncompleted reminders.
        """
        # Create multiple reminders with different states
        reminder_time = datetime.now(timezone.utc) + timedelta(hours=1)

        reminder1 = Reminder(
            reminder_time=reminder_time,
            message="First reminder",
            is_completed=False,
            tags=["first"],
        )

        reminder2 = Reminder(
            reminder_time=reminder_time + timedelta(hours=1),
            message="Second reminder",
            is_completed=True,
            tags=["second"],
        )

        reminder3 = Reminder(
            reminder_time=reminder_time + timedelta(hours=2),
            message="Third reminder",
            is_completed=False,
            tags=["third"],
            related_entity_type=EntityType.PERSON,
            related_entity_id=5,
        )

        test_session.add_all([reminder1, reminder2, reminder3])
        await test_session.commit()
        await test_session.refresh(reminder1)
        await test_session.refresh(reminder2)
        await test_session.refresh(reminder3)

        # Convert all reminders
        converter = ResultConverter()
        raw_results = {"reminders": [reminder1, reminder2, reminder3]}
        results = converter.convert_results(raw_results)

        # Validate the conversion
        assert len(results) == 3

        # First reminder (not completed)
        assert results[0].message == "First reminder"
        assert hasattr(results[0], "is_completed")
        assert results[0].is_completed is False

        # Second reminder (completed)
        assert results[1].message == "Second reminder"
        assert hasattr(results[1], "is_completed")
        assert results[1].is_completed is True

        # Third reminder (not completed, with entity)
        assert results[2].message == "Third reminder"
        assert hasattr(results[2], "is_completed")
        assert results[2].is_completed is False
        assert results[2].entity_type_attached == EntityType.PERSON
        assert results[2].entity_id_attached == 5
