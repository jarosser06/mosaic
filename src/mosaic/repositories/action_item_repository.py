"""ActionItem repository for task management."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.action_item import ActionItem
from ..models.base import ActionItemStatus, EntityType
from .base import BaseRepository


class ActionItemRepository(BaseRepository[ActionItem]):
    """Repository for ActionItem operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize action item repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, ActionItem)

    async def list_by_status(self, status: ActionItemStatus) -> list[ActionItem]:
        """
        List action items by status.

        Args:
            status: Action item status to filter by

        Returns:
            list[ActionItem]: Action items with the specified status
        """
        result = await self.session.execute(
            select(ActionItem)
            .where(ActionItem.status == status)
            .order_by(ActionItem.due_date.asc().nullslast(), ActionItem.id.asc())
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[ActionItem]:
        """
        List all active action items (PENDING or IN_PROGRESS).

        Returns:
            list[ActionItem]: All active action items
        """
        result = await self.session.execute(
            select(ActionItem)
            .where(ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS]))
            .order_by(ActionItem.due_date.asc().nullslast(), ActionItem.id.asc())
        )
        return list(result.scalars().all())

    async def list_overdue(self, current_time: datetime) -> list[ActionItem]:
        """
        List overdue active action items.

        Args:
            current_time: Current time to compare due dates against

        Returns:
            list[ActionItem]: Active action items with due_date < current_time
        """
        result = await self.session.execute(
            select(ActionItem)
            .where(ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS]))
            .where(ActionItem.due_date < current_time)
            .order_by(ActionItem.due_date.asc(), ActionItem.id.asc())
        )
        return list(result.scalars().all())

    async def list_by_entity(self, entity_type: EntityType, entity_id: int) -> list[ActionItem]:
        """
        List action items for a specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            list[ActionItem]: Action items for this entity
        """
        result = await self.session.execute(
            select(ActionItem)
            .where(ActionItem.entity_type == entity_type)
            .where(ActionItem.entity_id == entity_id)
            .order_by(ActionItem.due_date.asc().nullslast(), ActionItem.id.asc())
        )
        return list(result.scalars().all())

    async def mark_completed(self, id: int) -> Optional[ActionItem]:
        """
        Mark an action item as completed and set completed_at timestamp.

        Args:
            id: Action item ID

        Returns:
            Optional[ActionItem]: Updated action item if found, None otherwise
        """
        return await self.update(
            id, status=ActionItemStatus.COMPLETED, completed_at=datetime.now(timezone.utc)
        )

    async def update_status(self, id: int, status: ActionItemStatus) -> Optional[ActionItem]:
        """
        Update the status of an action item.

        If status is COMPLETED, also sets completed_at timestamp.

        Args:
            id: Action item ID
            status: New status

        Returns:
            Optional[ActionItem]: Updated action item if found, None otherwise
        """
        if status == ActionItemStatus.COMPLETED:
            return await self.update(id, status=status, completed_at=datetime.now(timezone.utc))
        else:
            return await self.update(id, status=status)
