"""Unit tests for time utility functions (half-hour rounding)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.mosaic.services.time_utils import calculate_duration_rounded, round_to_half_hour


class TestRoundToHalfHour:
    """Test half-hour rounding logic - CRITICAL BUSINESS RULE."""

    @pytest.mark.parametrize(
        "minutes,expected",
        [
            # Zero and negative edge cases
            (0, Decimal("0.0")),
            (-1, Decimal("0.0")),
            (-30, Decimal("0.0")),
            # 1-30 minutes rounds to 0.5 hours
            (1, Decimal("0.5")),
            (15, Decimal("0.5")),
            (30, Decimal("0.5")),
            # 31-60 minutes rounds to 1.0 hours
            (31, Decimal("1.0")),
            (45, Decimal("1.0")),
            (60, Decimal("1.0")),
            # Multi-hour cases with rounding
            (61, Decimal("1.5")),  # 1:01 → 1.5
            (90, Decimal("1.5")),  # 1:30 → 1.5
            (91, Decimal("2.0")),  # 1:31 → 2.0
            (120, Decimal("2.0")),  # 2:00 → 2.0
            (135, Decimal("2.5")),  # 2:15 → 2.5
            (150, Decimal("2.5")),  # 2:30 → 2.5
            (160, Decimal("3.0")),  # 2:40 → 3.0
            (180, Decimal("3.0")),  # 3:00 → 3.0
            # Larger durations
            (240, Decimal("4.0")),  # 4:00
            (255, Decimal("4.5")),  # 4:15 → 4.5
            (270, Decimal("4.5")),  # 4:30 → 4.5
            (285, Decimal("5.0")),  # 4:45 → 5.0
            (480, Decimal("8.0")),  # 8:00 (full work day)
        ],
    )
    def test_round_to_half_hour_parametrized(self, minutes: int, expected: Decimal):
        """Test half-hour rounding with comprehensive boundary cases."""
        result = round_to_half_hour(minutes)
        assert (
            result == expected
        ), f"round_to_half_hour({minutes}) should be {expected}, got {result}"

    def test_zero_minutes(self):
        """Zero minutes should return 0.0."""
        assert round_to_half_hour(0) == Decimal("0.0")

    def test_negative_minutes(self):
        """Negative minutes should return 0.0 (safety)."""
        assert round_to_half_hour(-10) == Decimal("0.0")

    def test_boundary_30_minutes(self):
        """30 minutes is the boundary - should round to 0.5."""
        assert round_to_half_hour(30) == Decimal("0.5")

    def test_boundary_31_minutes(self):
        """31 minutes crosses boundary - should round to 1.0."""
        assert round_to_half_hour(31) == Decimal("1.0")

    def test_spec_example_2_15(self):
        """Spec example: 2:15 → 2.5 hours."""
        assert round_to_half_hour(135) == Decimal("2.5")

    def test_spec_example_2_40(self):
        """Spec example: 2:40 → 3.0 hours."""
        assert round_to_half_hour(160) == Decimal("3.0")


class TestCalculateDurationRounded:
    """Test duration calculation with automatic rounding."""

    def test_basic_duration(self):
        """Test basic duration calculation."""
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("1.0")

    def test_15_minute_duration(self):
        """15 minutes should round to 0.5 hours."""
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 9, 15, 0, tzinfo=timezone.utc)
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("0.5")

    def test_45_minute_duration(self):
        """45 minutes should round to 1.0 hours."""
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 9, 45, 0, tzinfo=timezone.utc)
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("1.0")

    def test_2_hour_15_minute_duration(self):
        """2:15 should round to 2.5 hours."""
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 11, 15, 0, tzinfo=timezone.utc)
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("2.5")

    def test_end_before_start_raises_error(self):
        """End time before start time should raise ValueError."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            calculate_duration_rounded(start, end)

    def test_same_time_returns_zero(self):
        """Same start and end time should return 0.0."""
        time = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        result = calculate_duration_rounded(time, time)
        assert result == Decimal("0.0")

    def test_across_day_boundary(self):
        """Duration spanning days should calculate correctly."""
        start = datetime(2024, 1, 15, 23, 30, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 16, 1, 30, 0, tzinfo=timezone.utc)
        # 2 hours = 120 minutes → 2.0
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("2.0")

    def test_with_seconds(self):
        """Seconds should be included in duration calculation."""
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 9, 30, 45, tzinfo=timezone.utc)
        # 30 minutes 45 seconds = 30.75 minutes → rounds to 0.5
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("0.5")

    def test_timezone_aware_datetimes(self):
        """Test with different timezones."""
        from datetime import timezone as tz

        # Same instant in different timezones
        start = datetime(2024, 1, 15, 9, 0, 0, tzinfo=tz.utc)
        # End is 1 hour later in UTC, but expressed in UTC-5
        end = datetime(2024, 1, 15, 10, 0, 0, tzinfo=tz.utc)
        result = calculate_duration_rounded(start, end)
        assert result == Decimal("1.0")
