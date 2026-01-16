"""Gap analysis helpers for identifying missing work sessions.

This module provides functions to analyze work days and identify time gaps
where meetings occurred but no work sessions were logged.
"""

from datetime import date, timedelta
from typing import Optional

from ...models.meeting import Meeting
from ...models.work_session import WorkSession


class WorkDayGap:
    """
    Represents a day with meetings but no work sessions.

    Attributes:
        date: Date of the gap
        meetings: List of meetings on this date
        meeting_count: Number of meetings on this date
        total_meeting_minutes: Total minutes spent in meetings
    """

    def __init__(self, date: date, meetings: list[Meeting]):
        """
        Initialize work day gap.

        Args:
            date: Date of the gap
            meetings: Meetings on this date
        """
        self.date = date
        self.meetings = meetings
        self.meeting_count = len(meetings)
        self.total_meeting_minutes = sum(m.duration_minutes for m in meetings)


def analyze_work_day_gaps(
    work_sessions: list[WorkSession],
    meetings: list[Meeting],
    start_date: date,
    end_date: date,
) -> list[WorkDayGap]:
    """
    Identify days with meetings but no work sessions.

    This function helps identify potential missing time entries by finding
    dates where meetings occurred but no work was logged. This is useful for
    prompting users to fill in missing work sessions.

    Args:
        work_sessions: List of work sessions in the date range
        meetings: List of meetings in the date range
        start_date: Analysis start date (inclusive)
        end_date: Analysis end date (inclusive)

    Returns:
        list[WorkDayGap]: Gaps ordered by date (oldest first)

    Example:
        >>> gaps = analyze_work_day_gaps(sessions, meetings, start, end)
        >>> for gap in gaps:
        ...     print(f"{gap.date}: {gap.meeting_count} meetings, no work logged")
    """
    # Build set of dates with work sessions
    work_dates = {ws.date for ws in work_sessions}

    # Group meetings by date
    meetings_by_date: dict[date, list[Meeting]] = {}
    for meeting in meetings:
        meeting_date = meeting.start_time.date()
        # Only consider meetings within the date range
        if start_date <= meeting_date <= end_date:
            if meeting_date not in meetings_by_date:
                meetings_by_date[meeting_date] = []
            meetings_by_date[meeting_date].append(meeting)

    # Find gaps: dates with meetings but no work sessions
    gaps: list[WorkDayGap] = []
    for meeting_date, date_meetings in meetings_by_date.items():
        if meeting_date not in work_dates:
            gaps.append(WorkDayGap(meeting_date, date_meetings))

    # Sort by date (oldest first)
    gaps.sort(key=lambda g: g.date)
    return gaps


def format_gap_summary(gap: WorkDayGap) -> str:
    """
    Format a work day gap as a human-readable summary.

    Args:
        gap: Work day gap to format

    Returns:
        str: Formatted summary string

    Example:
        >>> gap = WorkDayGap(date(2024, 1, 15), meetings)
        >>> print(format_gap_summary(gap))
        2024-01-15: 3 meetings (90 minutes total), no work sessions logged
    """
    hours = gap.total_meeting_minutes / 60
    return (
        f"{gap.date.strftime('%Y-%m-%d')}: {gap.meeting_count} meeting(s) "
        f"({hours:.1f} hours total), no work sessions logged"
    )


def get_business_days_in_range(start_date: date, end_date: date) -> list[date]:
    """
    Get all business days (Monday-Friday) in a date range.

    Args:
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)

    Returns:
        list[date]: Business days in range

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    business_days: list[date] = []
    current = start_date

    while current <= end_date:
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Monday-Friday
            business_days.append(current)
        current += timedelta(days=1)

    return business_days


def find_missing_business_days(
    work_sessions: list[WorkSession],
    start_date: date,
    end_date: date,
    exclude_dates: Optional[list[date]] = None,
) -> list[date]:
    """
    Find business days with no work sessions logged.

    Args:
        work_sessions: List of work sessions in the date range
        start_date: Analysis start date (inclusive)
        end_date: Analysis end date (inclusive)
        exclude_dates: Optional list of dates to exclude (holidays, PTO, etc.)

    Returns:
        list[date]: Business days with no work sessions, ordered by date

    Example:
        >>> missing = find_missing_business_days(sessions, start, end)
        >>> for date in missing:
        ...     print(f"No work logged on {date}")
    """
    # Get all business days in range
    business_days = set(get_business_days_in_range(start_date, end_date))

    # Remove excluded dates
    if exclude_dates:
        business_days -= set(exclude_dates)

    # Remove dates with work sessions
    work_dates = {ws.date for ws in work_sessions}
    missing_dates = business_days - work_dates

    # Return sorted list
    return sorted(missing_dates)


def calculate_suggested_hours_from_meetings(meetings: list[Meeting]) -> float:
    """
    Calculate suggested work hours based on meeting duration.

    Uses a simple heuristic: round meeting time up to nearest half hour.
    This helps suggest minimum work session duration when meetings occurred
    but no work was logged.

    Args:
        meetings: List of meetings

    Returns:
        float: Suggested hours (in half-hour increments)

    Example:
        >>> meetings = [Meeting(duration_minutes=45), Meeting(duration_minutes=30)]
        >>> calculate_suggested_hours_from_meetings(meetings)
        1.5
    """
    total_minutes = sum(m.duration_minutes for m in meetings)

    # Round up to nearest 30 minutes
    if total_minutes == 0:
        return 0.0

    # Convert to half-hour increments (round up)
    half_hours = (total_minutes + 29) // 30  # Round up by adding 29 before integer division
    return half_hours * 0.5
