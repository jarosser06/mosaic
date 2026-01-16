"""Tests for meeting schemas (12 test cases)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.schemas.meeting import (
    LogMeetingInput,
    LogMeetingOutput,
    UpdateMeetingInput,
    UpdateMeetingOutput,
)


def test_log_meeting_input_valid():
    """Test valid LogMeetingInput creation."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)

    schema = LogMeetingInput(
        start_time=start,
        end_time=end,
        title="Sprint Planning",
        attendees=[1, 2, 3],
        project_id=42,
        description="Discussed Q1 roadmap",
        tags=["planning", "team"],
    )

    assert schema.start_time == start
    assert schema.end_time == end
    assert schema.title == "Sprint Planning"
    assert schema.attendees == [1, 2, 3]
    assert schema.project_id == 42
    assert schema.description == "Discussed Q1 roadmap"
    assert schema.privacy_level == PrivacyLevel.PRIVATE  # Default
    assert schema.tags == ["planning", "team"]


def test_log_meeting_input_privacy_default():
    """Test that privacy_level defaults to PRIVATE."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)

    schema = LogMeetingInput(
        start_time=start,
        end_time=end,
        title="Meeting",
    )

    assert schema.privacy_level == PrivacyLevel.PRIVATE


def test_log_meeting_input_rejects_naive_datetime():
    """Test that naive datetimes are rejected."""
    start = datetime(2026, 1, 15, 14, 0, 0)  # Naive
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogMeetingInput(start_time=start, end_time=end, title="Meeting")
    assert "Datetime must be timezone-aware" in str(exc_info.value)


def test_log_meeting_input_rejects_end_before_start():
    """Test that end_time before start_time is rejected."""
    start = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogMeetingInput(start_time=start, end_time=end, title="Meeting")
    assert "end_time must be after start_time" in str(exc_info.value)


def test_log_meeting_input_title_min_length():
    """Test that empty title is rejected."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        LogMeetingInput(start_time=start, end_time=end, title="")
    assert "at least 1 character" in str(exc_info.value).lower()


def test_log_meeting_input_title_max_length():
    """Test that title exceeding max_length is rejected."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    long_title = "x" * 256  # Exceeds 255 max

    with pytest.raises(ValidationError) as exc_info:
        LogMeetingInput(start_time=start, end_time=end, title=long_title)
    assert "at most 255 characters" in str(exc_info.value).lower()


def test_log_meeting_input_empty_attendees_default():
    """Test that attendees default to empty list."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)

    schema = LogMeetingInput(
        start_time=start,
        end_time=end,
        title="Meeting",
    )

    assert schema.attendees == []
    assert schema.tags == []


def test_log_meeting_output_valid():
    """Test valid LogMeetingOutput creation."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 14, 5, 0, tzinfo=timezone.utc)

    schema = LogMeetingOutput(
        id=1,
        start_time=start,
        end_time=end,
        title="Sprint Planning",
        attendees=[1, 2, 3],
        project_id=42,
        description="Notes",
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["planning"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.title == "Sprint Planning"
    assert schema.attendees == [1, 2, 3]


def test_update_meeting_input_partial_update():
    """Test UpdateMeetingInput with partial fields."""
    schema = UpdateMeetingInput(
        title="Updated Meeting",
        privacy_level=PrivacyLevel.INTERNAL,
    )

    assert schema.title == "Updated Meeting"
    assert schema.privacy_level == PrivacyLevel.INTERNAL
    assert schema.start_time is None
    assert schema.end_time is None


def test_update_meeting_input_validates_time_range():
    """Test that UpdateMeetingInput validates time range when both provided."""
    start = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        UpdateMeetingInput(start_time=start, end_time=end)
    assert "end_time must be after start_time" in str(exc_info.value)


def test_update_meeting_input_attendees_replacement():
    """Test that UpdateMeetingInput replaces attendees list."""
    schema = UpdateMeetingInput(attendees=[4, 5, 6])

    assert schema.attendees == [4, 5, 6]


def test_update_meeting_output_valid():
    """Test valid UpdateMeetingOutput creation."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 16, 0, 0, tzinfo=timezone.utc)

    schema = UpdateMeetingOutput(
        id=1,
        start_time=start,
        end_time=end,
        title="Updated Meeting",
        attendees=[1, 2, 3, 4],
        project_id=42,
        description="Updated notes",
        privacy_level=PrivacyLevel.INTERNAL,
        tags=["planning", "updated"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.title == "Updated Meeting"
    assert schema.privacy_level == PrivacyLevel.INTERNAL
