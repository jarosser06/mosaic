"""Service layer for scheduled tasks using APScheduler."""

import logging

from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import get_session
from .notification_service import NotificationService
from .reminder_service import ReminderService

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages scheduled tasks using APScheduler.

    Runs periodic jobs for checking and notifying about due reminders.
    """

    def __init__(self) -> None:
        """Initialize SchedulerService with AsyncScheduler."""
        self.scheduler = AsyncScheduler()
        self.notification_service = NotificationService()
        self._is_running = False

    async def start(self) -> None:
        """
        Start the scheduler with reminder check job.

        Schedules a job to run every minute that checks for due reminders
        and sends notifications.

        Raises:
            None
        """
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        # Enter the scheduler context (required by APScheduler 4.x)
        await self.scheduler.__aenter__()

        # Add reminder check job (runs every 1 minute)
        await self.scheduler.add_schedule(
            self._check_and_notify_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="check_reminders",
        )

        # Start the scheduler in background
        await self.scheduler.start_in_background()
        self._is_running = True
        logger.info("Scheduler started successfully")

    async def stop(self) -> None:
        """
        Stop the scheduler gracefully.

        Shuts down the scheduler and waits for running jobs to complete.

        Raises:
            None
        """
        if not self._is_running:
            logger.warning("Scheduler not running")
            return

        # Stop the scheduler
        await self.scheduler.stop()

        # Exit the scheduler context (required by APScheduler 4.x)
        await self.scheduler.__aexit__(None, None, None)

        self._is_running = False
        logger.info("Scheduler stopped successfully")

    async def _check_and_notify_reminders(self) -> None:
        """
        Job that checks for due reminders and sends notifications.

        This job runs every minute. It:
        1. Gets all due reminders (applying cooldown filter to prevent spam)
        2. Sends a notification for each due reminder
        3. Marks reminder as notified (updates last_notified_at)
        4. Auto-completes non-recurring reminders if configured

        Raises:
            None (logs errors instead of raising)
        """
        try:
            async with get_session() as session:
                reminder_service = ReminderService(session)

                # Get all due reminders (with cooldown filter applied)
                due_reminders = await reminder_service.check_due_reminders()

                if not due_reminders:
                    logger.debug("No due reminders found")
                    return

                logger.info(f"Found {len(due_reminders)} due reminders")

                # Send notification for each due reminder
                for reminder in due_reminders:
                    success = await self.notification_service.trigger_notification(
                        title="Reminder",
                        message=reminder.message,
                        metadata={
                            "reminder_id": reminder.id,
                            "reminder_time": reminder.reminder_time.isoformat(),
                            "related_entity_type": reminder.related_entity_type,
                            "related_entity_id": reminder.related_entity_id,
                        },
                    )

                    if success:
                        # Mark as notified to prevent spam
                        await reminder_service.mark_notified(reminder.id)
                        logger.info(
                            f"Notification sent successfully for reminder {reminder.id}, "
                            f"marked as notified"
                        )
                    else:
                        logger.error(f"Failed to send notification for reminder {reminder.id}")

                # Commit all changes
                await session.commit()

        except Exception as e:
            logger.error(f"Error in _check_and_notify_reminders: {e}", exc_info=True)
