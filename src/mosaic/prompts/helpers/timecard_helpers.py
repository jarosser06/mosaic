"""Timecard aggregation and formatting helpers.

This module provides functions for aggregating work sessions into timecard
entries and formatting them as markdown tables for external reporting.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.base import PrivacyLevel
from ...models.project import Project
from ...models.work_session import WorkSession


class TimecardEntry:
    """
    Aggregated timecard entry for one project on one date.

    Attributes:
        project_id: Project ID
        project_name: Project name
        date: Work date
        total_hours: Total hours worked on this project on this date
    """

    def __init__(self, project_id: int, project_name: str, date: date, total_hours: Decimal):
        """
        Initialize timecard entry.

        Args:
            project_id: Project ID
            project_name: Project name
            date: Work date
            total_hours: Total hours worked
        """
        self.project_id = project_id
        self.project_name = project_name
        self.date = date
        self.total_hours = total_hours


async def generate_timecard_entries(
    session: AsyncSession,
    start_date: date,
    end_date: date,
    employer_id: Optional[int] = None,
    privacy_filter: Optional[PrivacyLevel] = None,
) -> list[TimecardEntry]:
    """
    Generate timecard entries aggregating work sessions by project and date.

    This function creates one entry per project per date, summing all work
    session hours for that combination. This is the core logic for external
    timecard generation.

    Args:
        session: SQLAlchemy async session
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)
        employer_id: Optional employer ID to filter by project's employer
        privacy_filter: Optional privacy level filter (include this level and less restrictive)

    Returns:
        list[TimecardEntry]: Aggregated entries, ordered by date and project name

    Raises:
        ValueError: If end_date is before start_date

    Example:
        >>> entries = await generate_timecard_entries(
        ...     session,
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 7),
        ...     privacy_filter=PrivacyLevel.PUBLIC
        ... )
        >>> for entry in entries:
        ...     print(f"{entry.date} {entry.project_name}: {entry.total_hours}h")
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    # Build base query with aggregation
    query = (
        select(
            WorkSession.project_id,
            Project.name.label("project_name"),
            WorkSession.date,
            func.sum(WorkSession.duration_hours).label("total_hours"),
        )
        .join(Project, WorkSession.project_id == Project.id)
        .where(WorkSession.date >= start_date)
        .where(WorkSession.date <= end_date)
    )

    # Apply privacy filter if specified
    if privacy_filter is not None:
        if privacy_filter == PrivacyLevel.PUBLIC:
            query = query.where(WorkSession.privacy_level == PrivacyLevel.PUBLIC)
        elif privacy_filter == PrivacyLevel.INTERNAL:
            query = query.where(
                WorkSession.privacy_level.in_([PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL])
            )
        # For PRIVATE, include all (no filter needed)

    # Apply employer filter if specified
    if employer_id is not None:
        query = query.where(Project.on_behalf_of_id == employer_id)

    # Group by project and date
    query = query.group_by(WorkSession.project_id, Project.name, WorkSession.date).order_by(
        WorkSession.date, Project.name
    )

    result = await session.execute(query)

    # Convert rows to TimecardEntry objects
    return [
        TimecardEntry(
            project_id=row.project_id,
            project_name=row.project_name,
            date=row.date,
            total_hours=row.total_hours,
        )
        for row in result.all()
    ]


def format_timecard_markdown(entries: list[TimecardEntry]) -> str:
    """
    Format timecard entries as a markdown table.

    Args:
        entries: List of timecard entries to format

    Returns:
        str: Markdown formatted table with Date, Project, and Hours columns

    Example:
        >>> entries = [
        ...     TimecardEntry(1, "Project A", date(2024, 1, 15), Decimal("8.0")),
        ...     TimecardEntry(2, "Project B", date(2024, 1, 15), Decimal("2.5")),
        ... ]
        >>> print(format_timecard_markdown(entries))
        | Date       | Project   | Hours |
        |------------|-----------|-------|
        | 2024-01-15 | Project A | 8.0   |
        | 2024-01-15 | Project B | 2.5   |
    """
    if not entries:
        return "No timecard entries found."

    # Build markdown table
    lines = [
        "| Date       | Project   | Hours |",
        "|------------|-----------|-------|",
    ]

    for entry in entries:
        date_str = entry.date.strftime("%Y-%m-%d")
        # Format hours as decimal with 1 decimal place
        hours_str = f"{entry.total_hours:.1f}"
        lines.append(f"| {date_str} | {entry.project_name} | {hours_str} |")

    return "\n".join(lines)


def calculate_timecard_total(entries: list[TimecardEntry]) -> Decimal:
    """
    Calculate total hours across all timecard entries.

    Args:
        entries: List of timecard entries

    Returns:
        Decimal: Sum of all hours (0.0 if empty)
    """
    return sum((entry.total_hours for entry in entries), Decimal("0.0"))


def group_entries_by_project(entries: list[TimecardEntry]) -> dict[str, list[TimecardEntry]]:
    """
    Group timecard entries by project name.

    Args:
        entries: List of timecard entries

    Returns:
        dict[str, list[TimecardEntry]]: Entries grouped by project name
    """
    grouped: dict[str, list[TimecardEntry]] = {}
    for entry in entries:
        if entry.project_name not in grouped:
            grouped[entry.project_name] = []
        grouped[entry.project_name].append(entry)
    return grouped


def calculate_project_totals(entries: list[TimecardEntry]) -> dict[str, Decimal]:
    """
    Calculate total hours per project.

    Args:
        entries: List of timecard entries

    Returns:
        dict[str, Decimal]: Project name to total hours mapping
    """
    totals: dict[str, Decimal] = {}
    for entry in entries:
        if entry.project_name not in totals:
            totals[entry.project_name] = Decimal("0.0")
        totals[entry.project_name] += entry.total_hours
    return totals
