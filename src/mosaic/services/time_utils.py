"""Time utility functions for work session duration validation."""

from decimal import Decimal


def validate_duration_hours(duration: Decimal) -> None:
    """
    Validate duration_hours for direct input.

    Rules:
    - Must be positive (> 0)
    - Maximum 24 hours (sanity check)

    Args:
        duration: Duration in hours

    Raises:
        ValueError: If validation fails
    """
    if duration <= 0:
        raise ValueError("Duration must be greater than 0")
    if duration > 24:
        raise ValueError("Duration must not exceed 24 hours")
