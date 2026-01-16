"""Time utility functions for work session duration rounding."""

from datetime import datetime
from decimal import Decimal


def round_to_half_hour(minutes: int) -> Decimal:
    """
    Round duration to nearest 0.5 hours following spec rules.

    Rules from spec:
    - 0:01 to 0:30 minutes → 0.5 hours
    - 0:31 to 1:00 minutes → 1.0 hours
    - Examples: 2:15 → 2.5 hours, 2:40 → 3.0 hours

    Args:
        minutes: Total duration in minutes

    Returns:
        Decimal: Rounded hours with 1 decimal place
    """
    if minutes <= 0:
        return Decimal("0.0")

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return Decimal(str(float(hours)))
    elif remaining_minutes <= 30:
        return Decimal(str(float(hours) + 0.5))
    else:
        return Decimal(str(float(hours) + 1.0))


def calculate_duration_rounded(start_time: datetime, end_time: datetime) -> Decimal:
    """
    Calculate duration between times, rounded to half-hour precision.

    Args:
        start_time: Session start time
        end_time: Session end time

    Returns:
        Decimal: Rounded duration in hours

    Raises:
        ValueError: If end_time is before start_time
    """
    if end_time < start_time:
        raise ValueError("end_time must be after start_time")

    delta = end_time - start_time
    minutes = int(delta.total_seconds() / 60)
    return round_to_half_hour(minutes)
