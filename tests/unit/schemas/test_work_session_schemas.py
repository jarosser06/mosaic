"""Tests for work session schemas (12 test cases)."""

from datetime import datetime, timezone
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
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)

    schema = LogWorkSessionInput(
        start_time=start,
        end_time=end,
        project_id=42,
        description="Implemented feature X",
        tags=["backend", "api"],
    )

    assert schema.start_time == start
    assert schema.end_time == end
    assert schema.project_id == 42
    assert schema.description == "Implemented feature X"
    assert schema.privacy_level == PrivacyLevel.PRIVATE  # Default
    assert schema.tags == ["backend", "api"]


def test_log_work_session_input_privacy_default():
    """Test that privacy_level defaults to PRIVATE."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)

    schema = LogWorkSessionInput(
        start_time=start,
        end_time=end,
        project_id=1,
    )

    assert schema.privacy_level == PrivacyLevel.PRIVATE


def test_log_work_session_input_rejects_naive_datetime():
    """Test that naive datetimes are rejected."""
    start = datetime(2026, 1, 15, 9, 0, 0)  # Naive
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(start_time=start, end_time=end, project_id=1)
    assert "Datetime must be timezone-aware" in str(exc_info.value)


def test_log_work_session_input_rejects_end_before_start():
    """Test that end_time before start_time is rejected."""
    start = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(start_time=start, end_time=end, project_id=1)
    assert "end_time must be after start_time" in str(exc_info.value)


def test_log_work_session_input_rejects_invalid_project_id():
    """Test that project_id must be > 0."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(start_time=start, end_time=end, project_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


def test_log_work_session_input_description_max_length():
    """Test that description exceeding max_length is rejected."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    long_description = "x" * 2001  # Exceeds 2000 max

    with pytest.raises(ValidationError) as exc_info:
        LogWorkSessionInput(
            start_time=start,
            end_time=end,
            project_id=1,
            description=long_description,
        )
    assert "at most 2000 characters" in str(exc_info.value).lower()


def test_log_work_session_output_valid():
    """Test valid LogWorkSessionOutput creation."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 9, 5, 0, tzinfo=timezone.utc)

    schema = LogWorkSessionOutput(
        id=1,
        start_time=start,
        end_time=end,
        project_id=42,
        duration_hours=Decimal("8.0"),
        description="Implemented feature X",
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["backend"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
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
    assert schema.start_time is None
    assert schema.end_time is None
    assert schema.project_id is None


def test_update_work_session_input_validates_time_range():
    """Test that UpdateWorkSessionInput validates time range when both provided."""
    start = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        UpdateWorkSessionInput(start_time=start, end_time=end)
    assert "end_time must be after start_time" in str(exc_info.value)


def test_update_work_session_input_allows_only_start_or_end():
    """Test that UpdateWorkSessionInput allows only start_time or only end_time."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)

    # Only start_time is valid (validation happens when both are present)
    schema = UpdateWorkSessionInput(start_time=start)
    assert schema.start_time == start
    assert schema.end_time is None


def test_update_work_session_output_valid():
    """Test valid UpdateWorkSessionOutput creation."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = UpdateWorkSessionOutput(
        id=1,
        start_time=start,
        end_time=end,
        project_id=42,
        duration_hours=Decimal("8.0"),
        description="Updated work",
        privacy_level=PrivacyLevel.INTERNAL,
        tags=["backend", "updated"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.privacy_level == PrivacyLevel.INTERNAL
    assert schema.tags == ["backend", "updated"]


def test_log_work_session_input_empty_tags_default():
    """Test that tags default to empty list."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)

    schema = LogWorkSessionInput(
        start_time=start,
        end_time=end,
        project_id=1,
    )

    assert schema.tags == []
