"""Unit tests for ReminderRepository time-based queries."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType
from src.mosaic.models.project import Project
from src.mosaic.models.reminder import Reminder
from src.mosaic.repositories.reminder_repository import ReminderRepository


class TestReminderRepositoryBasicQueries:
    """Test basic ReminderRepository query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> ReminderRepository:
        """Create reminder repository."""
        return ReminderRepository(session)

    @pytest.mark.asyncio
    async def test_list_active_reminders_only(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test listing only active (not completed) reminders."""
        # Create mixed reminders
        active1 = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Active Reminder 1",
            is_completed=False,
        )
        active2 = Reminder(
            reminder_time=datetime(2024, 1, 21, 14, 0, tzinfo=timezone.utc),
            message="Active Reminder 2",
            is_completed=False,
        )
        completed = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Completed Reminder",
            is_completed=True,
        )
        session.add_all([active1, active2, completed])
        await session.flush()

        # List active only
        results = await repo.list_active()

        assert len(results) == 2
        messages = {r.message for r in results}
        assert "Active Reminder 1" in messages
        assert "Active Reminder 2" in messages
        assert "Completed Reminder" not in messages

    @pytest.mark.asyncio
    async def test_list_active_empty(self, repo: ReminderRepository):
        """Test listing active reminders when none exist."""
        result = await repo.list_active()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_due_reminders(self, repo: ReminderRepository, session: AsyncSession):
        """Test listing reminders due before specific time."""
        # Create reminders with different due times
        early = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Early Reminder",
            is_completed=False,
        )
        mid = Reminder(
            reminder_time=datetime(2024, 1, 20, 14, 0, tzinfo=timezone.utc),
            message="Mid Reminder",
            is_completed=False,
        )
        late = Reminder(
            reminder_time=datetime(2024, 1, 25, 16, 0, tzinfo=timezone.utc),
            message="Late Reminder",
            is_completed=False,
        )
        session.add_all([early, mid, late])
        await session.flush()

        # Get reminders due before Jan 21
        results = await repo.list_due_reminders(datetime(2024, 1, 21, 0, 0, tzinfo=timezone.utc))

        assert len(results) == 2
        messages = {r.message for r in results}
        assert "Early Reminder" in messages
        assert "Mid Reminder" in messages
        assert "Late Reminder" not in messages

    @pytest.mark.asyncio
    async def test_list_due_reminders_excludes_completed(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test due reminders excludes completed ones."""
        # Create due but completed reminder
        completed = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Completed Due Reminder",
            is_completed=True,
        )
        session.add(completed)
        await session.flush()

        # Get reminders due before Jan 20
        results = await repo.list_due_reminders(datetime(2024, 1, 20, 0, 0, tzinfo=timezone.utc))

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_list_due_reminders_excludes_snoozed(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test due reminders excludes snoozed ones."""
        # Create reminder due now but snoozed until later
        snoozed = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Snoozed Reminder",
            snoozed_until=datetime(2024, 1, 25, 10, 0, tzinfo=timezone.utc),
            is_completed=False,
        )
        session.add(snoozed)
        await session.flush()

        # Get reminders due before Jan 20 (should not include snoozed)
        results = await repo.list_due_reminders(datetime(2024, 1, 20, 0, 0, tzinfo=timezone.utc))

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_list_due_reminders_includes_snooze_expired(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test due reminders includes reminders whose snooze has expired."""
        # Create reminder snoozed until Jan 18
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            message="Snooze Expired",
            snoozed_until=datetime(2024, 1, 18, 10, 0, tzinfo=timezone.utc),
            is_completed=False,
        )
        session.add(reminder)
        await session.flush()

        # Get reminders due before Jan 20 (snooze expired, should include)
        results = await repo.list_due_reminders(datetime(2024, 1, 20, 0, 0, tzinfo=timezone.utc))

        assert len(results) == 1
        assert results[0].message == "Snooze Expired"

    @pytest.mark.asyncio
    async def test_list_by_entity(
        self,
        repo: ReminderRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test listing reminders for a specific entity."""
        # Create reminders for project and other entity
        project_reminder1 = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Project Reminder 1",
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        project_reminder2 = Reminder(
            reminder_time=datetime(2024, 1, 21, 14, 0, tzinfo=timezone.utc),
            message="Project Reminder 2",
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )
        other_reminder = Reminder(
            reminder_time=datetime(2024, 1, 22, 9, 0, tzinfo=timezone.utc),
            message="Other Reminder",
            related_entity_type=EntityType.MEETING,
            related_entity_id=999,
        )
        session.add_all([project_reminder1, project_reminder2, other_reminder])
        await session.flush()

        # List reminders for project
        results = await repo.list_by_entity(EntityType.PROJECT, project.id)

        assert len(results) == 2
        messages = {r.message for r in results}
        assert "Project Reminder 1" in messages
        assert "Project Reminder 2" in messages
        assert "Other Reminder" not in messages


class TestReminderRepositoryActions:
    """Test reminder action methods (mark completed, snooze)."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> ReminderRepository:
        """Create reminder repository."""
        return ReminderRepository(session)

    @pytest.fixture
    async def test_reminder(self, session: AsyncSession) -> Reminder:
        """Create test reminder."""
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Test Reminder",
            is_completed=False,
        )
        session.add(reminder)
        await session.flush()
        await session.refresh(reminder)
        return reminder

    @pytest.mark.asyncio
    async def test_mark_completed(
        self, repo: ReminderRepository, session: AsyncSession, test_reminder: Reminder
    ):
        """Test marking reminder as completed."""
        # Mark completed
        updated = await repo.mark_completed(test_reminder.id)

        assert updated is not None
        assert updated.is_completed is True

        # Verify not in active list
        active = await repo.list_active()
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_mark_completed_nonexistent(self, repo: ReminderRepository):
        """Test marking non-existent reminder returns None."""
        result = await repo.mark_completed(999999)
        assert result is None

    @pytest.mark.asyncio
    async def test_snooze_reminder(
        self, repo: ReminderRepository, session: AsyncSession, test_reminder: Reminder
    ):
        """Test snoozing reminder until specific time."""
        snooze_until = datetime(2024, 1, 25, 10, 0, tzinfo=timezone.utc)

        # Snooze reminder
        updated = await repo.snooze(test_reminder.id, snooze_until)

        assert updated is not None
        assert updated.snoozed_until == snooze_until

        # Verify not in due list before snooze expires
        due = await repo.list_due_reminders(datetime(2024, 1, 24, 0, 0, tzinfo=timezone.utc))
        assert len(due) == 0

    @pytest.mark.asyncio
    async def test_snooze_nonexistent(self, repo: ReminderRepository):
        """Test snoozing non-existent reminder returns None."""
        result = await repo.snooze(999999, datetime(2024, 1, 25, 10, 0, tzinfo=timezone.utc))
        assert result is None

    @pytest.mark.asyncio
    async def test_create_reminder_with_entity(
        self,
        repo: ReminderRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating reminder linked to entity."""
        reminder = await repo.create(
            reminder_time=datetime(2024, 2, 1, 17, 0, tzinfo=timezone.utc),
            message="Project Deadline - Final deliverable due",
            related_entity_type=EntityType.PROJECT,
            related_entity_id=project.id,
        )

        assert reminder.id is not None
        assert reminder.message == "Project Deadline - Final deliverable due"
        assert reminder.related_entity_type == EntityType.PROJECT
        assert reminder.related_entity_id == project.id
        assert reminder.is_completed is False

    @pytest.mark.asyncio
    async def test_update_reminder_due_time(
        self, repo: ReminderRepository, session: AsyncSession, test_reminder: Reminder
    ):
        """Test updating reminder due time."""
        new_reminder_time = datetime(2024, 1, 25, 15, 0, tzinfo=timezone.utc)

        # Update due time
        updated = await repo.update(test_reminder.id, reminder_time=new_reminder_time)

        assert updated is not None
        assert updated.reminder_time == new_reminder_time

    @pytest.mark.asyncio
    async def test_reminder_lifecycle(self, repo: ReminderRepository, session: AsyncSession):
        """Test complete reminder lifecycle: create, snooze, complete."""
        # Create reminder
        reminder = await repo.create(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Lifecycle Test",
        )

        # Verify in active list
        active = await repo.list_active()
        assert len(active) == 1

        # Snooze it
        await repo.snooze(reminder.id, datetime(2024, 1, 25, 10, 0, tzinfo=timezone.utc))

        # Still in active list (just snoozed, not completed)
        active = await repo.list_active()
        assert len(active) == 1

        # Mark completed
        await repo.mark_completed(reminder.id)

        # No longer in active list
        active = await repo.list_active()
        assert len(active) == 0


class TestReminderNotificationCooldown:
    """Test notification cooldown feature to prevent spam."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> ReminderRepository:
        """Create reminder repository."""
        return ReminderRepository(session)

    @pytest.mark.asyncio
    async def test_list_due_reminders_with_cooldown_excludes_recently_notified(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test cooldown filter excludes reminders notified within cooldown period."""
        # Create reminder due now, notified 30 minutes ago
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Recently Notified",
            is_completed=False,
            last_notified_at=datetime(2024, 1, 20, 9, 30, tzinfo=timezone.utc),
        )
        session.add(reminder)
        await session.flush()

        # Query with cooldown threshold of 10:00 (1 hour ago)
        # Reminder was notified at 9:30, which is within cooldown
        cooldown_since = datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc)
        results = await repo.list_due_reminders(
            before_time=datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc),
            cooldown_since=cooldown_since,
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_list_due_reminders_with_cooldown_includes_cooldown_expired(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test cooldown filter includes reminders notified outside cooldown period."""
        # Create reminder due now, notified 2 hours ago
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Cooldown Expired",
            is_completed=False,
            last_notified_at=datetime(2024, 1, 20, 8, 0, tzinfo=timezone.utc),
        )
        session.add(reminder)
        await session.flush()

        # Query with cooldown threshold of 9:00 (1 hour ago)
        # Reminder was notified at 8:00, which is before cooldown
        cooldown_since = datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc)
        results = await repo.list_due_reminders(
            before_time=datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc),
            cooldown_since=cooldown_since,
        )

        assert len(results) == 1
        assert results[0].message == "Cooldown Expired"

    @pytest.mark.asyncio
    async def test_list_due_reminders_with_cooldown_includes_never_notified(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test cooldown filter includes reminders never notified."""
        # Create reminder due now, never notified
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Never Notified",
            is_completed=False,
            last_notified_at=None,
        )
        session.add(reminder)
        await session.flush()

        # Query with cooldown threshold
        cooldown_since = datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc)
        results = await repo.list_due_reminders(
            before_time=datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc),
            cooldown_since=cooldown_since,
        )

        assert len(results) == 1
        assert results[0].message == "Never Notified"

    @pytest.mark.asyncio
    async def test_list_due_reminders_without_cooldown_returns_all(
        self, repo: ReminderRepository, session: AsyncSession
    ):
        """Test without cooldown parameter returns all due reminders."""
        # Create reminder due now, notified recently
        reminder = Reminder(
            reminder_time=datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            message="Recently Notified",
            is_completed=False,
            last_notified_at=datetime(2024, 1, 20, 9, 30, tzinfo=timezone.utc),
        )
        session.add(reminder)
        await session.flush()

        # Query WITHOUT cooldown filter
        results = await repo.list_due_reminders(
            before_time=datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc)
        )

        # Should include all due reminders, regardless of notification time
        assert len(results) == 1
