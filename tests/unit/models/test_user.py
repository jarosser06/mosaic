"""Tests for User model."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import WeekBoundary
from src.mosaic.models.user import User


@pytest.mark.asyncio
async def test_user_creation_minimal(session: AsyncSession) -> None:
    """Test creating user with minimal required fields."""
    user = User(full_name="Jane Doe")
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.id is not None
    assert user.full_name == "Jane Doe"
    assert user.timezone == "UTC"
    assert user.week_boundary == WeekBoundary.MONDAY_FRIDAY
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_creation_full(session: AsyncSession) -> None:
    """Test creating user with all fields populated."""
    profile_updated = datetime(2024, 1, 10, tzinfo=timezone.utc)

    user = User(
        full_name="John Smith",
        email="john@example.com",
        phone="+1234567890",
        timezone="America/New_York",
        week_boundary=WeekBoundary.SUNDAY_SATURDAY,
        working_hours_start=9,
        working_hours_end=17,
        communication_style="Direct and concise",
        work_approach="Test-driven development",
        profile_last_updated=profile_updated,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.full_name == "John Smith"
    assert user.email == "john@example.com"
    assert user.phone == "+1234567890"
    assert user.timezone == "America/New_York"
    assert user.week_boundary == WeekBoundary.SUNDAY_SATURDAY
    assert user.working_hours_start == 9
    assert user.working_hours_end == 17
    assert user.communication_style == "Direct and concise"
    assert user.work_approach == "Test-driven development"
    assert user.profile_last_updated == profile_updated


@pytest.mark.asyncio
async def test_user_optional_fields_null(session: AsyncSession) -> None:
    """Test that optional fields can be None."""
    user = User(full_name="Test User")
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.email is None
    assert user.phone is None
    assert user.working_hours_start is None
    assert user.working_hours_end is None
    assert user.communication_style is None
    assert user.work_approach is None
    assert user.profile_last_updated is None


@pytest.mark.parametrize(
    "week_boundary",
    [
        WeekBoundary.MONDAY_FRIDAY,
        WeekBoundary.SUNDAY_SATURDAY,
        WeekBoundary.MONDAY_SUNDAY,
    ],
)
@pytest.mark.asyncio
async def test_user_week_boundary_values(
    session: AsyncSession, week_boundary: WeekBoundary
) -> None:
    """Test all valid week boundary values."""
    user = User(full_name="Test User", week_boundary=week_boundary)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.week_boundary == week_boundary


@pytest.mark.parametrize(
    "start_hour,end_hour",
    [
        (0, 24),
        (9, 17),
        (6, 14),
        (12, 20),
    ],
)
@pytest.mark.asyncio
async def test_user_working_hours_range(
    session: AsyncSession, start_hour: int, end_hour: int
) -> None:
    """Test various working hour ranges."""
    user = User(
        full_name="Test User",
        working_hours_start=start_hour,
        working_hours_end=end_hour,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.working_hours_start == start_hour
    assert user.working_hours_end == end_hour


@pytest.mark.asyncio
async def test_user_timezone_custom(session: AsyncSession) -> None:
    """Test setting custom timezone."""
    user = User(full_name="Test User", timezone="Europe/London")
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.timezone == "Europe/London"


@pytest.mark.asyncio
async def test_user_update_profile(session: AsyncSession) -> None:
    """Test updating user profile fields."""
    user = User(full_name="Original Name")
    session.add(user)
    await session.flush()
    await session.refresh(user)

    original_updated = user.updated_at

    user.full_name = "Updated Name"
    user.email = "newemail@example.com"
    user.communication_style = "Updated style"
    await session.flush()
    await session.refresh(user)

    assert user.full_name == "Updated Name"
    assert user.email == "newemail@example.com"
    assert user.communication_style == "Updated style"
    assert user.updated_at >= original_updated


@pytest.mark.asyncio
async def test_user_long_text_fields(session: AsyncSession) -> None:
    """Test that long text fields accept appropriate length strings."""
    long_style = "x" * 1000
    long_approach = "y" * 1000

    user = User(
        full_name="Test User",
        communication_style=long_style,
        work_approach=long_approach,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert len(user.communication_style) == 1000
    assert len(user.work_approach) == 1000
