"""Unit tests for UserRepository custom queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import WeekBoundary
from src.mosaic.models.user import User
from src.mosaic.repositories.user_repository import UserRepository


class TestUserRepositoryQueries:
    """Test UserRepository custom query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> UserRepository:
        """Create user repository."""
        return UserRepository(session)

    async def test_get_by_email_existing(self, repo: UserRepository, session: AsyncSession):
        """Test finding user by email when exists."""
        # Create user
        user = User(
            full_name="John Doe",
            email="john@example.com",
            timezone="America/New_York",
        )
        session.add(user)
        await session.flush()

        # Find by email
        result = await repo.get_by_email("john@example.com")

        assert result is not None
        assert result.email == "john@example.com"
        assert result.full_name == "John Doe"

    async def test_get_by_email_nonexistent(self, repo: UserRepository):
        """Test finding user by email returns None when not found."""
        result = await repo.get_by_email("nonexistent@example.com")
        assert result is None

    async def test_get_by_email_case_sensitive(self, repo: UserRepository, session: AsyncSession):
        """Test email lookup is case-sensitive."""
        # Create user
        user = User(
            full_name="Test User",
            email="Test@Example.COM",
        )
        session.add(user)
        await session.flush()

        # Exact match should work
        result = await repo.get_by_email("Test@Example.COM")
        assert result is not None

        # Different case should not match
        result = await repo.get_by_email("test@example.com")
        assert result is None

    async def test_create_user_with_preferences(self, repo: UserRepository, session: AsyncSession):
        """Test creating user with full preferences."""
        user = await repo.create(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="+1-555-0123",
            timezone="America/Los_Angeles",
            week_boundary=WeekBoundary.SUNDAY_SATURDAY,
            working_hours_start=9,
            working_hours_end=17,
            communication_style="Direct and concise",
            work_approach="Test-driven development",
        )

        assert user.id is not None
        assert user.full_name == "Jane Smith"
        assert user.timezone == "America/Los_Angeles"
        assert user.week_boundary == WeekBoundary.SUNDAY_SATURDAY
        assert user.working_hours_start == 9
        assert user.working_hours_end == 17

    async def test_update_user_timezone(self, repo: UserRepository, session: AsyncSession):
        """Test updating user timezone preference."""
        # Create user
        user = await repo.create(
            full_name="Test User",
            email="test@example.com",
            timezone="UTC",
        )
        user_id = user.id

        # Update timezone
        updated = await repo.update(user_id, timezone="Europe/London")

        assert updated is not None
        assert updated.timezone == "Europe/London"
        assert updated.email == "test@example.com"  # Other fields unchanged

    async def test_update_week_boundary(self, repo: UserRepository, session: AsyncSession):
        """Test updating week boundary preference."""
        # Create user with default week boundary
        user = await repo.create(
            full_name="Test User",
            email="test@example.com",
        )
        assert user.week_boundary == WeekBoundary.MONDAY_FRIDAY

        # Update to Sunday-Saturday
        updated = await repo.update(user.id, week_boundary=WeekBoundary.SUNDAY_SATURDAY)

        assert updated is not None
        assert updated.week_boundary == WeekBoundary.SUNDAY_SATURDAY

    async def test_multiple_users_different_emails(
        self, repo: UserRepository, session: AsyncSession
    ):
        """Test creating multiple users with different emails."""
        # Create multiple users
        user1 = await repo.create(full_name="User One", email="user1@example.com")
        user2 = await repo.create(full_name="User Two", email="user2@example.com")

        # Verify both can be retrieved
        result1 = await repo.get_by_email("user1@example.com")
        result2 = await repo.get_by_email("user2@example.com")

        assert result1 is not None
        assert result1.id == user1.id
        assert result2 is not None
        assert result2.id == user2.id
