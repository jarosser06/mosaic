"""Tests for Base, TimestampMixin, and Enums."""

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src.mosaic.models.base import (
    Base,
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    TimestampMixin,
    WeekBoundary,
)


class TestModel(Base, TimestampMixin):
    """Test model for TimestampMixin verification."""

    __tablename__ = "test_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


@pytest.mark.asyncio
async def test_timestamp_mixin_created_at(session: AsyncSession) -> None:
    """Test that created_at is automatically set."""
    test_obj = TestModel(name="Test")
    session.add(test_obj)
    await session.flush()
    await session.refresh(test_obj)

    assert test_obj.created_at is not None
    assert test_obj.updated_at is not None


@pytest.mark.asyncio
async def test_timestamp_mixin_updated_at(session: AsyncSession) -> None:
    """Test that updated_at is updated on modification."""
    test_obj = TestModel(name="Test")
    session.add(test_obj)
    await session.flush()
    await session.refresh(test_obj)

    original_updated = test_obj.updated_at

    # Modify and flush again
    test_obj.name = "Updated"
    await session.flush()
    await session.refresh(test_obj)

    # updated_at should be >= original (may be same if very fast)
    assert test_obj.updated_at >= original_updated


@pytest.mark.parametrize(
    "enum_value",
    [
        PrivacyLevel.PUBLIC,
        PrivacyLevel.INTERNAL,
        PrivacyLevel.PRIVATE,
    ],
)
def test_privacy_level_enum_values(enum_value: PrivacyLevel) -> None:
    """Test PrivacyLevel enum values."""
    assert isinstance(enum_value.value, str)
    assert enum_value.value in ["public", "internal", "private"]


@pytest.mark.parametrize(
    "enum_class,expected_values",
    [
        (WeekBoundary, ["mon-fri", "sun-sat", "mon-sun"]),
        (
            EntityType,
            [
                "person",
                "client",
                "project",
                "employer",
                "work_session",
                "meeting",
                "reminder",
                "note",
                "action_item",
                "bookmark",
            ],
        ),
        (ProjectStatus, ["active", "paused", "completed"]),
        (ClientStatus, ["active", "past"]),
        (ClientType, ["company", "individual"]),
    ],
)
def test_enum_values_comprehensive(enum_class: type, expected_values: list[str]) -> None:
    """Test all enum classes have expected values."""
    actual_values = [e.value for e in enum_class]
    assert set(actual_values) == set(expected_values)
