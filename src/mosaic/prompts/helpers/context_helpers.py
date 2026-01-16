"""MCP message context helpers for prompt formatting.

This module provides functions for creating MCP-compliant message structures
and formatting utilities for dates, durations, and other common data types.
"""

from datetime import date, datetime, timedelta  # noqa: F401
from decimal import Decimal
from typing import Any, Optional


def create_user_message(content: str) -> dict[str, Any]:
    """
    Create an MCP user message structure.

    Args:
        content: Message content text

    Returns:
        dict[str, Any]: MCP-compliant user message

    Example:
        >>> msg = create_user_message("What did I work on today?")
        >>> msg
        {'role': 'user', 'content': {'type': 'text', 'text': 'What did I work on today?'}}
    """
    return {
        "role": "user",
        "content": {
            "type": "text",
            "text": content,
        },
    }


def create_assistant_message(content: str) -> dict[str, Any]:
    """
    Create an MCP assistant message structure.

    Args:
        content: Message content text

    Returns:
        dict[str, Any]: MCP-compliant assistant message

    Example:
        >>> msg = create_assistant_message("You worked on Project A for 8 hours.")
        >>> msg
        {'role': 'assistant', 'content': {'type': 'text', 'text': 'You worked on...'}}
    """
    return {
        "role": "assistant",
        "content": {
            "type": "text",
            "text": content,
        },
    }


def create_message_list(*messages: str, alternate_roles: bool = True) -> list[dict[str, Any]]:
    """
    Create a list of MCP messages with alternating roles.

    Args:
        *messages: Variable number of message content strings
        alternate_roles: If True, alternate between user and assistant (default True)

    Returns:
        list[dict[str, Any]]: List of MCP messages

    Example:
        >>> msgs = create_message_list(
        ...     "What did I work on?",
        ...     "You worked on Project A.",
        ...     "How many hours?"
        ... )
        >>> len(msgs)
        3
        >>> msgs[0]['role']
        'user'
        >>> msgs[1]['role']
        'assistant'
    """
    if not alternate_roles:
        # All user messages
        return [create_user_message(msg) for msg in messages]

    # Alternate between user and assistant
    result: list[dict[str, Any]] = []
    for i, content in enumerate(messages):
        if i % 2 == 0:
            result.append(create_user_message(content))
        else:
            result.append(create_assistant_message(content))
    return result


def format_date_range(start_date: date, end_date: date) -> str:
    """
    Format a date range as a human-readable string.

    Args:
        start_date: Range start date
        end_date: Range end date

    Returns:
        str: Formatted date range

    Example:
        >>> format_date_range(date(2024, 1, 1), date(2024, 1, 7))
        '2024-01-01 to 2024-01-07'
        >>> format_date_range(date(2024, 1, 15), date(2024, 1, 15))
        '2024-01-15'
    """
    if start_date == end_date:
        return start_date.strftime("%Y-%m-%d")
    return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"


def format_duration_hours(hours: Decimal) -> str:
    """
    Format duration in hours as a human-readable string.

    Args:
        hours: Duration in hours

    Returns:
        str: Formatted duration string

    Example:
        >>> format_duration_hours(Decimal("8.0"))
        '8.0 hours'
        >>> format_duration_hours(Decimal("1.5"))
        '1.5 hours'
        >>> format_duration_hours(Decimal("0.5"))
        '0.5 hours'
    """
    return f"{hours:.1f} hours"


def format_duration_minutes(minutes: int) -> str:
    """
    Format duration in minutes as a human-readable string.

    Converts to hours and minutes if >= 60 minutes.

    Args:
        minutes: Duration in minutes

    Returns:
        str: Formatted duration string

    Example:
        >>> format_duration_minutes(30)
        '30 minutes'
        >>> format_duration_minutes(90)
        '1 hour 30 minutes'
        >>> format_duration_minutes(120)
        '2 hours'
    """
    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"

    return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minutes"


def format_datetime(dt: datetime, include_timezone: bool = False) -> str:
    """
    Format datetime as a human-readable string.

    Args:
        dt: Datetime to format
        include_timezone: Whether to include timezone info (default False)

    Returns:
        str: Formatted datetime string

    Example:
        >>> dt = datetime(2024, 1, 15, 14, 30)
        >>> format_datetime(dt)
        '2024-01-15 14:30'
        >>> format_datetime(dt, include_timezone=True)
        '2024-01-15 14:30:00+00:00'
    """
    if include_timezone:
        return dt.isoformat()
    return dt.strftime("%Y-%m-%d %H:%M")


def format_date(d: date) -> str:
    """
    Format date as a human-readable string.

    Args:
        d: Date to format

    Returns:
        str: Formatted date string (YYYY-MM-DD)

    Example:
        >>> format_date(date(2024, 1, 15))
        '2024-01-15'
    """
    return d.strftime("%Y-%m-%d")


def get_relative_date_description(target_date: date, reference_date: Optional[date] = None) -> str:
    """
    Get a relative description of a date (e.g., "today", "yesterday").

    Args:
        target_date: Date to describe
        reference_date: Reference date for comparison (defaults to today)

    Returns:
        str: Relative date description

    Example:
        >>> ref = date(2024, 1, 15)
        >>> get_relative_date_description(ref, ref)
        'today'
        >>> get_relative_date_description(ref - timedelta(days=1), ref)
        'yesterday'
        >>> get_relative_date_description(ref + timedelta(days=1), ref)
        'tomorrow'
    """
    if reference_date is None:
        reference_date = date.today()

    delta = (target_date - reference_date).days

    if delta == 0:
        return "today"
    elif delta == -1:
        return "yesterday"
    elif delta == 1:
        return "tomorrow"
    elif -7 < delta < 0:
        return f"{abs(delta)} days ago"
    elif 0 < delta < 7:
        return f"in {delta} days"
    else:
        return format_date(target_date)


def create_context_summary(
    work_session_count: int,
    meeting_count: int,
    note_count: int,
    date_range: tuple[date, date],
) -> str:
    """
    Create a summary of context data for prompt inclusion.

    Args:
        work_session_count: Number of work sessions
        meeting_count: Number of meetings
        note_count: Number of notes
        date_range: Tuple of (start_date, end_date)

    Returns:
        str: Formatted context summary

    Example:
        >>> summary = create_context_summary(
        ...     work_session_count=15,
        ...     meeting_count=8,
        ...     note_count=5,
        ...     date_range=(date(2024, 1, 1), date(2024, 1, 7))
        ... )
        >>> print(summary)
        Context data for 2024-01-01 to 2024-01-07:
        - 15 work sessions
        - 8 meetings
        - 5 notes
    """
    start_date, end_date = date_range
    lines = [
        f"Context data for {format_date_range(start_date, end_date)}:",
        f"- {work_session_count} work session{'s' if work_session_count != 1 else ''}",
        f"- {meeting_count} meeting{'s' if meeting_count != 1 else ''}",
        f"- {note_count} note{'s' if note_count != 1 else ''}",
    ]
    return "\n".join(lines)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated (default "...")

    Returns:
        str: Truncated text

    Example:
        >>> truncate_text("This is a long text", 10)
        'This is...'
        >>> truncate_text("Short", 10)
        'Short'
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix
