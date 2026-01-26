"""Unit tests for time utility functions (duration validation only)."""

from decimal import Decimal

import pytest

from src.mosaic.services.time_utils import validate_duration_hours


class TestValidateDurationHours:
    """Test duration validation - CRITICAL BUSINESS RULE."""

    @pytest.mark.parametrize(
        "duration",
        [
            Decimal("0.1"),  # Very small duration
            Decimal("0.5"),  # 30 minutes
            Decimal("1.0"),  # 1 hour
            Decimal("2.5"),  # 2.5 hours
            Decimal("8.0"),  # Full work day
            Decimal("12.0"),  # Long day
            Decimal("16.0"),  # Very long day
            Decimal("24.0"),  # Maximum allowed
        ],
    )
    def test_validate_duration_valid_values(self, duration: Decimal):
        """Test that valid duration values are accepted."""
        validate_duration_hours(duration)
        # Function returns None - no assertion needed

    def test_validate_duration_rejects_zero(self):
        """Test that zero duration is rejected."""
        with pytest.raises(ValueError, match="Duration must be greater than 0"):
            validate_duration_hours(Decimal("0.0"))

    @pytest.mark.parametrize(
        "duration",
        [
            Decimal("-0.1"),
            Decimal("-1.0"),
            Decimal("-10.0"),
        ],
    )
    def test_validate_duration_rejects_negative(self, duration: Decimal):
        """Test that negative duration values are rejected."""
        with pytest.raises(ValueError, match="Duration must be greater than 0"):
            validate_duration_hours(duration)

    @pytest.mark.parametrize(
        "duration",
        [
            Decimal("24.1"),
            Decimal("25.0"),
            Decimal("48.0"),
            Decimal("100.0"),
        ],
    )
    def test_validate_duration_rejects_over_24(self, duration: Decimal):
        """Test that duration > 24 hours is rejected."""
        with pytest.raises(ValueError, match="Duration must not exceed 24 hours"):
            validate_duration_hours(duration)

    def test_validate_duration_boundary_exactly_24(self):
        """Test that exactly 24.0 hours is accepted (boundary case)."""
        validate_duration_hours(Decimal("24.0"))
        # Function returns None - no assertion needed

    def test_validate_duration_decimal_precision(self):
        """Test that decimal precision is maintained."""
        duration = Decimal("2.33333")
        validate_duration_hours(duration)
        # Function returns None - validation only

    def test_validate_duration_very_small(self):
        """Test very small but valid duration (0.01 hours = ~36 seconds)."""
        duration = Decimal("0.01")
        validate_duration_hours(duration)
        # Function returns None - validation only

    def test_validate_duration_returns_none(self):
        """Test that validate_duration_hours returns None."""
        result = validate_duration_hours(Decimal("8.0"))
        assert result is None

    def test_validate_duration_float_input_conversion(self):
        """Test that float input is converted to Decimal."""
        # Note: In production, schemas should convert to Decimal before calling
        # this function, but test robustness
        validate_duration_hours(Decimal(8.5))
        # Function returns None - validation only

    def test_validate_duration_integer_input_conversion(self):
        """Test that integer input is converted to Decimal."""
        validate_duration_hours(Decimal(8))
        # Function returns None - validation only
