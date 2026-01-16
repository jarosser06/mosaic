"""Service layer for reminder operations with recurrence support."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.reminder import Reminder
from ..repositories.reminder_repository import ReminderRepository


class ReminderService:
    """
    Business logic for reminder operations.

    Handles reminder creation, completion, snoozing, and recurrence calculation.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize ReminderService.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.repository = ReminderRepository(session)
        self.session = session

    async def create_reminder(
        self,
        reminder_time: datetime,
        message: str,
        recurrence_config: dict[str, Any] | None = None,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
        tags: list[str] | None = None,
    ) -> Reminder:
        """
        Create a new reminder.

        Args:
            reminder_time: When the reminder should trigger
            message: Reminder text/message
            recurrence_config: Optional recurrence configuration (daily/weekly/monthly)
            related_entity_type: Optional entity type this reminder relates to
            related_entity_id: Optional entity ID this reminder relates to
            tags: Optional tags for categorization

        Returns:
            Reminder: Created reminder instance

        Raises:
            ValueError: If recurrence_config is invalid
        """
        # Validate recurrence config if provided
        if recurrence_config is not None:
            self._validate_recurrence_config(recurrence_config)

        reminder = Reminder(
            reminder_time=reminder_time,
            message=message,
            is_completed=False,
            recurrence_config=recurrence_config,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            tags=tags or [],
        )

        self.session.add(reminder)
        await self.session.flush()
        return reminder

    async def complete_reminder(self, reminder_id: int) -> Reminder | None:
        """
        Mark a reminder as completed and create next occurrence if recurring.

        Args:
            reminder_id: ID of the reminder to complete

        Returns:
            Reminder | None: The next occurrence for recurring reminders, or None for non-recurring

        Raises:
            ValueError: If reminder not found
        """
        reminder = await self.repository.get_by_id(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder with ID {reminder_id} not found")

        # Mark as completed
        reminder.is_completed = True
        reminder.snoozed_until = None

        next_reminder = None
        # If recurring, create next occurrence
        if reminder.recurrence_config:
            next_reminder_time = self._calculate_next_occurrence(
                reminder.reminder_time, reminder.recurrence_config
            )
            if next_reminder_time:
                next_reminder = Reminder(
                    reminder_time=next_reminder_time,
                    message=reminder.message,
                    is_completed=False,
                    recurrence_config=reminder.recurrence_config,
                    related_entity_type=reminder.related_entity_type,
                    related_entity_id=reminder.related_entity_id,
                    tags=reminder.tags or [],
                )
                self.session.add(next_reminder)
                await self.session.flush()
                await self.session.refresh(next_reminder)

        await self.session.flush()
        await self.session.refresh(reminder)
        return next_reminder

    async def snooze_reminder(self, reminder_id: int, snooze_until: datetime) -> Reminder:
        """
        Snooze a reminder until a specified time.

        Args:
            reminder_id: ID of the reminder to snooze
            snooze_until: When the reminder should trigger again

        Returns:
            Reminder: Updated reminder instance

        Raises:
            ValueError: If reminder not found or snooze_until is before reminder time
        """
        reminder = await self.repository.get_by_id(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder with ID {reminder_id} not found")

        # Validate snooze_until is after the original reminder time
        if snooze_until <= reminder.reminder_time:
            raise ValueError("snooze_until must be in the future")

        reminder.snoozed_until = snooze_until
        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def check_due_reminders(self) -> list[Reminder]:
        """
        Get all reminders that are due now (not completed, reminder_time <= now, not snoozed).

        Returns:
            list[Reminder]: List of due reminders

        Raises:
            None
        """
        now = datetime.now(datetime.now().astimezone().tzinfo)
        return await self.repository.list_due_reminders(now)

    def _validate_recurrence_config(self, config: dict[str, Any]) -> None:
        """
        Validate recurrence configuration.

        Args:
            config: Recurrence configuration dictionary

        Raises:
            ValueError: If config is invalid
        """
        if "frequency" not in config:
            raise ValueError("recurrence_config must contain 'frequency' key")

        valid_frequencies = ["daily", "weekly", "monthly"]
        if config["frequency"] not in valid_frequencies:
            raise ValueError(
                f"frequency must be one of {valid_frequencies}, got {config['frequency']}"
            )

        # Validate weekly config
        if config["frequency"] == "weekly":
            if "day_of_week" not in config:
                raise ValueError("weekly recurrence requires 'day_of_week' (0-6)")
            day = config["day_of_week"]
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError("day_of_week must be an integer 0-6 (Mon-Sun)")

        # Validate monthly config
        if config["frequency"] == "monthly":
            if "day_of_month" not in config:
                raise ValueError("monthly recurrence requires 'day_of_month' (1-31)")
            day = config["day_of_month"]
            if not isinstance(day, int) or day < 1 or day > 31:
                raise ValueError("day_of_month must be an integer 1-31")

    def _calculate_next_occurrence(
        self, current_reminder_time: datetime, config: dict[str, Any]
    ) -> datetime | None:
        """
        Calculate next occurrence time based on recurrence config.

        Args:
            current_reminder_time: Current reminder time
            config: Recurrence configuration

        Returns:
            datetime | None: Next occurrence time, or None if cannot calculate

        Raises:
            ValueError: If config is invalid
        """
        frequency = config.get("frequency")

        if frequency == "daily":
            # Add one day
            return current_reminder_time + timedelta(days=1)

        elif frequency == "weekly":
            # Add one week
            return current_reminder_time + timedelta(weeks=1)

        elif frequency == "monthly":
            # Add one month (handle variable month lengths)
            day_of_month = config.get("day_of_month", current_reminder_time.day)

            # Move to next month
            if current_reminder_time.month == 12:
                next_year = current_reminder_time.year + 1
                next_month = 1
            else:
                next_year = current_reminder_time.year
                next_month = current_reminder_time.month + 1

            # Handle day overflow (e.g., Jan 31 -> Feb 28)
            import calendar

            max_day = calendar.monthrange(next_year, next_month)[1]
            actual_day = min(day_of_month, max_day)

            return current_reminder_time.replace(year=next_year, month=next_month, day=actual_day)

        return None
