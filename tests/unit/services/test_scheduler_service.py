"""Unit tests for SchedulerService with APScheduler."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mosaic.services.scheduler_service import SchedulerService


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_scheduler_successfully(self):
        """Test starting scheduler adds reminder check job."""
        # Create a mock scheduler
        mock_scheduler = AsyncMock()
        mock_scheduler.__aenter__ = AsyncMock()
        mock_scheduler.add_schedule = AsyncMock()
        mock_scheduler.start_in_background = AsyncMock()

        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()
            await service.start()

            assert service._is_running is True
            mock_scheduler.__aenter__.assert_called_once()
            mock_scheduler.add_schedule.assert_called_once()
            mock_scheduler.start_in_background.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_scheduler_already_running_logs_warning(self):
        """Test starting already-running scheduler logs warning."""
        mock_scheduler = AsyncMock()
        mock_scheduler.__aenter__ = AsyncMock()
        mock_scheduler.add_schedule = AsyncMock()

        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()
            service._is_running = True

            await service.start()

            # Should not call add_schedule if already running
            mock_scheduler.__aenter__.assert_not_called()
            mock_scheduler.add_schedule.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_scheduler_successfully(self):
        """Test stopping scheduler."""
        mock_scheduler = AsyncMock()
        mock_scheduler.stop = AsyncMock()
        mock_scheduler.__aexit__ = AsyncMock()

        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()
            service._is_running = True

            await service.stop()

            assert service._is_running is False
            mock_scheduler.stop.assert_called_once()
            mock_scheduler.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_stop_scheduler_not_running_logs_warning(self):
        """Test stopping non-running scheduler logs warning."""
        mock_scheduler = AsyncMock()
        mock_scheduler.stop = AsyncMock()

        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()
            service._is_running = False

            await service.stop()

            # Should not call stop if not running
            mock_scheduler.stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_scheduler_interval_configured_correctly(self):
        """Test reminder check job scheduled with correct interval."""
        mock_scheduler = AsyncMock()
        mock_scheduler.__aenter__ = AsyncMock()
        mock_scheduler.add_schedule = AsyncMock()
        mock_scheduler.start_in_background = AsyncMock()

        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()
            await service.start()

            # Verify add_schedule called with correct parameters
            mock_scheduler.add_schedule.assert_called_once()
            call_args = mock_scheduler.add_schedule.call_args
            assert call_args[1]["id"] == "check_reminders"
            # Check trigger is IntervalTrigger with 1 minute
            trigger = call_args[1]["trigger"]
            assert trigger.minutes == 1


class TestReminderCheckJob:
    """Test _check_and_notify_reminders job logic."""

    @pytest.mark.asyncio
    async def test_check_and_notify_reminders_sends_notifications(self):
        """Test job sends notifications for due reminders."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            # Mock reminder
            mock_reminder = MagicMock()
            mock_reminder.id = 123
            mock_reminder.message = "Test reminder"
            mock_reminder.reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
            mock_reminder.related_entity_type = "project"
            mock_reminder.related_entity_id = 456

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                with patch(
                    "src.mosaic.services.scheduler_service.ReminderService"
                ) as mock_reminder_service_class:
                    # Mock session
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Mock ReminderService
                    mock_reminder_service = AsyncMock()
                    mock_reminder_service.check_due_reminders.return_value = [mock_reminder]
                    mock_reminder_service_class.return_value = mock_reminder_service

                    # Mock notification service
                    service.notification_service.trigger_notification = AsyncMock(return_value=True)

                    await service._check_and_notify_reminders()

                    # Verify notification sent
                    service.notification_service.trigger_notification.assert_called_once_with(
                        title="Reminder",
                        message="Test reminder",
                        metadata={
                            "reminder_id": 123,
                            "reminder_time": mock_reminder.reminder_time.isoformat(),
                            "related_entity_type": "project",
                            "related_entity_id": 456,
                        },
                    )

    @pytest.mark.asyncio
    async def test_check_and_notify_reminders_no_reminders(self):
        """Test job handles no due reminders gracefully."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                with patch(
                    "src.mosaic.services.scheduler_service.ReminderService"
                ) as mock_reminder_service_class:
                    # Mock session
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Mock ReminderService - no reminders
                    mock_reminder_service = AsyncMock()
                    mock_reminder_service.check_due_reminders.return_value = []
                    mock_reminder_service_class.return_value = mock_reminder_service

                    # Mock notification service
                    service.notification_service.trigger_notification = AsyncMock()

                    await service._check_and_notify_reminders()

                    # Verify no notifications sent
                    service.notification_service.trigger_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_notify_reminders_handles_notification_failure(self):
        """Test job handles notification failure gracefully."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            # Mock reminder
            mock_reminder = MagicMock()
            mock_reminder.id = 123
            mock_reminder.message = "Test reminder"
            mock_reminder.reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
            mock_reminder.related_entity_type = None
            mock_reminder.related_entity_id = None

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                with patch(
                    "src.mosaic.services.scheduler_service.ReminderService"
                ) as mock_reminder_service_class:
                    # Mock session
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Mock ReminderService
                    mock_reminder_service = AsyncMock()
                    mock_reminder_service.check_due_reminders.return_value = [mock_reminder]
                    mock_reminder_service_class.return_value = mock_reminder_service

                    # Mock notification service - failure
                    service.notification_service.trigger_notification = AsyncMock(
                        return_value=False
                    )

                    # Should not raise exception
                    await service._check_and_notify_reminders()

    @pytest.mark.asyncio
    async def test_check_and_notify_reminders_handles_exception(self):
        """Test job catches and logs exceptions."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                # Mock session raises exception
                mock_get_session.return_value.__aenter__.side_effect = Exception("Database error")

                # Should not raise exception
                await service._check_and_notify_reminders()

    @pytest.mark.asyncio
    async def test_check_and_notify_reminders_multiple_reminders(self):
        """Test job sends notifications for multiple reminders."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            # Mock multiple reminders
            mock_reminder1 = MagicMock()
            mock_reminder1.id = 1
            mock_reminder1.message = "Reminder 1"
            mock_reminder1.reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
            mock_reminder1.related_entity_type = None
            mock_reminder1.related_entity_id = None

            mock_reminder2 = MagicMock()
            mock_reminder2.id = 2
            mock_reminder2.message = "Reminder 2"
            mock_reminder2.reminder_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
            mock_reminder2.related_entity_type = None
            mock_reminder2.related_entity_id = None

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                with patch(
                    "src.mosaic.services.scheduler_service.ReminderService"
                ) as mock_reminder_service_class:
                    # Mock session
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Mock ReminderService
                    mock_reminder_service = AsyncMock()
                    mock_reminder_service.check_due_reminders.return_value = [
                        mock_reminder1,
                        mock_reminder2,
                    ]
                    mock_reminder_service_class.return_value = mock_reminder_service

                    # Mock notification service
                    service.notification_service.trigger_notification = AsyncMock(return_value=True)

                    await service._check_and_notify_reminders()

                    # Verify notifications sent for both
                    assert service.notification_service.trigger_notification.call_count == 2


class TestIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_scheduler_does_not_auto_complete_reminders(self):
        """Test scheduler only notifies, does not complete reminders."""
        # Mock scheduler
        mock_scheduler = AsyncMock()
        with patch(
            "src.mosaic.services.scheduler_service.AsyncScheduler", return_value=mock_scheduler
        ):
            service = SchedulerService()

            # Mock reminder
            mock_reminder = MagicMock()
            mock_reminder.id = 123
            mock_reminder.message = "Test reminder"
            mock_reminder.reminder_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
            mock_reminder.related_entity_type = None
            mock_reminder.related_entity_id = None

            with patch("src.mosaic.services.scheduler_service.get_session") as mock_get_session:
                with patch(
                    "src.mosaic.services.scheduler_service.ReminderService"
                ) as mock_reminder_service_class:
                    # Mock session
                    mock_session = AsyncMock()
                    mock_get_session.return_value.__aenter__.return_value = mock_session

                    # Mock ReminderService
                    mock_reminder_service = AsyncMock()
                    mock_reminder_service.check_due_reminders.return_value = [mock_reminder]
                    mock_reminder_service.complete_reminder = AsyncMock()
                    mock_reminder_service_class.return_value = mock_reminder_service

                    # Mock notification service
                    service.notification_service.trigger_notification = AsyncMock(return_value=True)

                    await service._check_and_notify_reminders()

                    # Verify complete_reminder was NOT called
                    mock_reminder_service.complete_reminder.assert_not_called()
