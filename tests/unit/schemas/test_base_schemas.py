"""Tests for base schema mixins and validators (8 test cases)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.mosaic.schemas.common import (
    BaseSchema,
    DateRangeMixin,
    TimeRangeMixin,
    TimezoneAwareDatetimeMixin,
)


class SampleTimezoneAwareSchema(BaseSchema, TimezoneAwareDatetimeMixin):
    """Sample schema for testing timezone-aware validation."""

    event_time: datetime


class SampleTimeRangeSchema(BaseSchema, TimezoneAwareDatetimeMixin, TimeRangeMixin):
    """Sample schema for testing time range validation."""

    start_time: datetime
    end_time: datetime


class SampleDateRangeSchema(BaseSchema, DateRangeMixin):
    """Sample schema for testing date range validation."""

    start_date: datetime
    end_date: datetime


def test_timezone_aware_accepts_aware_datetime():
    """Test that timezone-aware validator accepts aware datetimes."""
    aware_dt = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    schema = SampleTimezoneAwareSchema(event_time=aware_dt)
    assert schema.event_time == aware_dt


def test_timezone_aware_rejects_naive_datetime():
    """Test that timezone-aware validator rejects naive datetimes."""
    naive_dt = datetime(2026, 1, 15, 10, 0, 0)
    with pytest.raises(ValidationError) as exc_info:
        SampleTimezoneAwareSchema(event_time=naive_dt)
    assert "Datetime must be timezone-aware" in str(exc_info.value)


def test_time_range_valid_range():
    """Test that TimeRangeMixin accepts valid time ranges (end > start)."""
    start = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    schema = SampleTimeRangeSchema(start_time=start, end_time=end)
    assert schema.start_time == start
    assert schema.end_time == end


def test_time_range_rejects_end_before_start():
    """Test that TimeRangeMixin rejects end_time before start_time."""
    start = datetime(2026, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        SampleTimeRangeSchema(start_time=start, end_time=end)
    assert "end_time must be after start_time" in str(exc_info.value)


def test_time_range_rejects_end_equal_start():
    """Test that TimeRangeMixin rejects end_time equal to start_time."""
    same_time = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        SampleTimeRangeSchema(start_time=same_time, end_time=same_time)
    assert "end_time must be after start_time" in str(exc_info.value)


def test_date_range_valid_range():
    """Test that DateRangeMixin accepts valid date ranges (end >= start)."""
    start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
    schema = SampleDateRangeSchema(start_date=start, end_date=end)
    assert schema.start_date == start
    assert schema.end_date == end


def test_date_range_accepts_equal_dates():
    """Test that DateRangeMixin accepts end_date equal to start_date."""
    same_date = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    schema = SampleDateRangeSchema(start_date=same_date, end_date=same_date)
    assert schema.start_date == same_date
    assert schema.end_date == same_date


def test_date_range_rejects_end_before_start():
    """Test that DateRangeMixin rejects end_date before start_date."""
    start = datetime(2026, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        SampleDateRangeSchema(start_date=start, end_date=end)
    assert "end_date must be on or after start_date" in str(exc_info.value)
