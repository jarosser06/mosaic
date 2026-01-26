"""Tests for work session schemas (simplified: date + duration only)."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.schemas.work_session import (
    LogWorkSessionInput,
    LogWorkSessionOutput,
    UpdateWorkSessionInput,
    UpdateWorkSessionOutput,
)


def test_log_work_session_input_valid():
    """Test valid LogWorkSessionInput creation."""
    work_date = date(2026, 1, 15)

    schema = LogWorkSessionInput(
        date=work_date,
        duration_hours=Decimal("8.0"),
        project_id=42,
        description="Implemented feature X",
        tags=["backend", "api"],
    )

    assert schema.date == work_date
    assert schema.duration_hours == Decimal("8.0")
    assert schema.project_id == 42
    assert schema.description == "Implemented feature X"
    assert schema.privacy_level == PrivacyLevel.PRIVATE  # Default
    assert schema.tags == ["backend", "api"]


def test_log_work_session_input_privacy_default():
    """Test that privacy_level defaults to PRIVATE."""
    schema = LogWorkSessionInput(
        date=date(2026, 1, 15),
        duration_hours=Decimal("8.0"),
        project_id=1,
    )

    assert schema.privacy_level == PrivacyLevel.PRIVATE


@pytest.mark.parametrize(
    "duration",
    [
        Decimal("0.1"),  # Very small
        Decimal("0.5"),  # 30 minutes
        Decimal("1.0"),  # 1 hour
        Decimal("8.0"),  # Full day
        Decimal("16.0"),  # Long day
        Decimal("24.0"),  # Maximum
    ],
)
def test_log_work_session_input_valid_durations(duration: Decimal):
    """Test that valid duration values are accepted."""
    schema = LogWorkSessionInput(
        date=date(2026, 1, 15),
        duration_hours=duration,
        project_id=1,
    )

    assert schema.duration_hours == duration


def test_log_work_session_input_rejects_zero_duration():
    """Test that zero duration is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("0.0"),
            project_id=1,
        )
    assert "greater than 0" in str(exc_info.value).lower()


def test_log_work_session_input_rejects_negative_duration():
    """Test that negative duration is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("-1.0"),
            project_id=1,
        )
    assert "greater than 0" in str(exc_info.value).lower()


def test_log_work_session_input_rejects_duration_over_24():
    """Test that duration > 24 hours is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("24.1"),
            project_id=1,
        )
    assert "less than or equal to 24" in str(exc_info.value).lower()


def test_log_work_session_input_accepts_exactly_24_hours():
    """Test that exactly 24.0 hours is accepted (boundary case)."""
    schema = LogWorkSessionInput(
        date=date(2026, 1, 15),
        duration_hours=Decimal("24.0"),
        project_id=1,
    )

    assert schema.duration_hours == Decimal("24.0")


def test_log_work_session_input_rejects_invalid_project_id():
    """Test that project_id must be > 0."""
    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("8.0"),
            project_id=0,
        )
    assert "greater than 0" in str(exc_info.value).lower()


def test_log_work_session_input_description_max_length():
    """Test that description exceeding max_length is rejected."""
    long_description = "x" * 2001  # Exceeds 2000 max

    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("8.0"),
            project_id=1,
            description=long_description,
        )
    assert "at most 2000 characters" in str(exc_info.value).lower()


def test_log_work_session_input_tags_default():
    """Test that tags default to empty list."""
    schema = LogWorkSessionInput(
        date=date(2026, 1, 15),
        duration_hours=Decimal("8.0"),
        project_id=1,
    )

    assert schema.tags == []


def test_log_work_session_output_valid():
    """Test valid LogWorkSessionOutput creation."""
    work_date = date(2026, 1, 15)
    created = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 9, 5, 0, tzinfo=timezone.utc)

    schema = LogWorkSessionOutput(
        id=1,
        date=work_date,
        project_id=42,
        duration_hours=Decimal("8.0"),
        description="Implemented feature X",
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["backend"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.date == work_date
    assert schema.duration_hours == Decimal("8.0")
    assert schema.privacy_level == PrivacyLevel.PRIVATE


def test_update_work_session_input_partial_update():
    """Test UpdateWorkSessionInput with partial fields."""
    schema = UpdateWorkSessionInput(
        description="Updated description",
        privacy_level=PrivacyLevel.INTERNAL,
    )

    assert schema.description == "Updated description"
    assert schema.privacy_level == PrivacyLevel.INTERNAL
    assert schema.date is None
    assert schema.duration_hours is None
    assert schema.project_id is None


def test_update_work_session_input_update_duration():
    """Test UpdateWorkSessionInput can update duration with validation."""
    schema = UpdateWorkSessionInput(duration_hours=Decimal("4.5"))

    assert schema.duration_hours == Decimal("4.5")


def test_update_work_session_input_rejects_invalid_duration():
    """Test that UpdateWorkSessionInput validates duration when provided."""
    with pytest.raises(ValidationError) as exc_info:
        UpdateWorkSessionInput(duration_hours=Decimal("25.0"))  # > 24 hours
    assert "less than or equal to 24" in str(exc_info.value).lower()


def test_update_work_session_input_all_fields_optional():
    """Test that UpdateWorkSessionInput allows all fields to be None."""
    schema = UpdateWorkSessionInput()

    assert schema.date is None
    assert schema.duration_hours is None
    assert schema.project_id is None
    assert schema.description is None
    assert schema.privacy_level is None
    assert schema.tags is None


def test_update_work_session_output_valid():
    """Test valid UpdateWorkSessionOutput creation."""
    work_date = date(2026, 1, 15)
    created = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = UpdateWorkSessionOutput(
        id=1,
        date=work_date,
        project_id=42,
        duration_hours=Decimal("8.0"),
        description="Updated work",
        privacy_level=PrivacyLevel.INTERNAL,
        tags=["backend", "updated"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.date == work_date
    assert schema.privacy_level == PrivacyLevel.INTERNAL
    assert schema.tags == ["backend", "updated"]


def test_log_work_session_input_decimal_precision():
    """Test that duration_hours maintains decimal precision."""
    schema = LogWorkSessionInput(
        date=date(2026, 1, 15),
        duration_hours=Decimal("2.33333"),
        project_id=1,
    )

    assert schema.duration_hours == Decimal("2.33333")
