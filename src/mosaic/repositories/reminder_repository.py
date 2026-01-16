"""Reminder repository for time-based notifications."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import EntityType
from ..models.reminder import Reminder
from .base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    """Repository for Reminder operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize reminder repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Reminder)

    async def list_active(self) -> list[Reminder]:
        """
        List all active (not completed) reminders.

        Returns:
            list[Reminder]: All active reminders
        """
        result = await self.session.execute(
            select(Reminder).where(Reminder.is_completed == False)  # noqa: E712
        )
        return list(result.scalars().all())

    async def list_due_reminders(self, before_time: datetime) -> list[Reminder]:
        """
        List reminders due before a specific time (not completed, not snoozed).

        Args:
            before_time: Time threshold

        Returns:
            list[Reminder]: Reminders due before this time
        """
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.is_completed == False)  # noqa: E712
            .where(Reminder.reminder_time <= before_time)
            .where((Reminder.snoozed_until.is_(None)) | (Reminder.snoozed_until <= before_time))
        )
        return list(result.scalars().all())

    async def list_by_entity(self, entity_type: EntityType, entity_id: int) -> list[Reminder]:
        """
        List reminders for a specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            list[Reminder]: Reminders for this entity
        """
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.related_entity_type == entity_type)
            .where(Reminder.related_entity_id == entity_id)
        )
        return list(result.scalars().all())

    async def mark_completed(self, id: int) -> Optional[Reminder]:
        """
        Mark a reminder as completed.

        Args:
            id: Reminder ID

        Returns:
            Optional[Reminder]: Updated reminder if found, None otherwise
        """
        return await self.update(id, is_completed=True)

    async def snooze(self, id: int, until: datetime) -> Optional[Reminder]:
        """
        Snooze a reminder until a specific time.

        Args:
            id: Reminder ID
            until: Time to snooze until

        Returns:
            Optional[Reminder]: Updated reminder if found, None otherwise
        """
        return await self.update(id, snoozed_until=until)
