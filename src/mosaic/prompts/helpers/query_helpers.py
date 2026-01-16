"""Database query helpers for prompt context building.

This module provides reusable database query functions for retrieving
work sessions, meetings, notes, and project information needed across
multiple MCP prompt handlers.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ...models.base import EntityType, PrivacyLevel
from ...models.meeting import Meeting, MeetingAttendee
from ...models.note import Note
from ...models.project import Project
from ...models.work_session import WorkSession


async def get_work_sessions_by_date_range(
    session: AsyncSession,
    start_date: date,
    end_date: date,
    employer_id: Optional[int] = None,
    privacy_filter: Optional[PrivacyLevel] = None,
) -> list[WorkSession]:
    """
    Get work sessions within a date range with optional filtering.

    Args:
        session: SQLAlchemy async session
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)
        employer_id: Optional employer ID to filter by project's employer
        privacy_filter: Optional privacy level filter (include this level and less restrictive)

    Returns:
        list[WorkSession]: Work sessions matching criteria, with project eagerly loaded

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    query = (
        select(WorkSession)
        .where(WorkSession.date >= start_date)
        .where(WorkSession.date <= end_date)
        .options(joinedload(WorkSession.project))
        .order_by(WorkSession.date, WorkSession.start_time)
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
        query = query.join(Project).where(Project.on_behalf_of_id == employer_id)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_meetings_by_date_range(
    session: AsyncSession,
    start_date: date,
    end_date: date,
    person_id: Optional[int] = None,
    privacy_filter: Optional[PrivacyLevel] = None,
) -> list[Meeting]:
    """
    Get meetings within a date range with optional filtering.

    Args:
        session: SQLAlchemy async session
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)
        person_id: Optional person ID to filter by attendees
        privacy_filter: Optional privacy level filter (include this level and less restrictive)

    Returns:
        list[Meeting]: Meetings matching criteria, with project and attendees eagerly loaded

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    # Convert dates to datetime boundaries
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    query = (
        select(Meeting)
        .where(Meeting.start_time >= start_datetime)
        .where(Meeting.start_time <= end_datetime)
        .options(
            joinedload(Meeting.project),
            selectinload(Meeting.attendees).selectinload(MeetingAttendee.person),
        )
        .order_by(Meeting.start_time)
    )

    # Apply privacy filter if specified
    if privacy_filter is not None:
        if privacy_filter == PrivacyLevel.PUBLIC:
            query = query.where(Meeting.privacy_level == PrivacyLevel.PUBLIC)
        elif privacy_filter == PrivacyLevel.INTERNAL:
            query = query.where(
                Meeting.privacy_level.in_([PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL])
            )
        # For PRIVATE, include all (no filter needed)

    # Apply person filter if specified
    if person_id is not None:
        query = query.join(MeetingAttendee).where(MeetingAttendee.person_id == person_id)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_recent_project_notes(
    session: AsyncSession,
    project_id: int,
    limit: int = 10,
    privacy_filter: Optional[PrivacyLevel] = None,
) -> list[Note]:
    """
    Get recent notes for a project.

    Args:
        session: SQLAlchemy async session
        project_id: Project ID
        limit: Maximum number of notes to return (default 10)
        privacy_filter: Optional privacy level filter (include this level and less restrictive)

    Returns:
        list[Note]: Recent notes for the project, ordered by creation time (newest first)
    """
    query = (
        select(Note)
        .where(Note.entity_type == EntityType.PROJECT)
        .where(Note.entity_id == project_id)
        .order_by(Note.created_at.desc(), Note.id.desc())
        .limit(limit)
    )

    # Apply privacy filter if specified
    if privacy_filter is not None:
        if privacy_filter == PrivacyLevel.PUBLIC:
            query = query.where(Note.privacy_level == PrivacyLevel.PUBLIC)
        elif privacy_filter == PrivacyLevel.INTERNAL:
            query = query.where(
                Note.privacy_level.in_([PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL])
            )
        # For PRIVATE, include all (no filter needed)

    result = await session.execute(query)
    return list(result.scalars().all())


async def calculate_total_hours_by_project(
    session: AsyncSession,
    project_id: int,
    start_date: date,
    end_date: date,
) -> Decimal:
    """
    Calculate total hours worked on a project in a date range.

    Args:
        session: SQLAlchemy async session
        project_id: Project ID
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)

    Returns:
        Decimal: Total hours worked (0.0 if no sessions)

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    result = await session.execute(
        select(func.sum(WorkSession.duration_hours))
        .where(WorkSession.project_id == project_id)
        .where(WorkSession.date >= start_date)
        .where(WorkSession.date <= end_date)
    )
    total = result.scalar_one()
    return total if total is not None else Decimal("0.0")


async def get_projects_worked_on_in_range(
    session: AsyncSession,
    start_date: date,
    end_date: date,
    employer_id: Optional[int] = None,
) -> list[Project]:
    """
    Get all projects with work sessions in a date range.

    Args:
        session: SQLAlchemy async session
        start_date: Range start date (inclusive)
        end_date: Range end date (inclusive)
        employer_id: Optional employer ID to filter by

    Returns:
        list[Project]: Projects with work in the date range, with employer/client loaded

    Raises:
        ValueError: If end_date is before start_date
    """
    if end_date < start_date:
        raise ValueError("end_date must be after start_date")

    query = (
        select(Project)
        .join(WorkSession)
        .where(WorkSession.date >= start_date)
        .where(WorkSession.date <= end_date)
        .options(joinedload(Project.employer), joinedload(Project.client))
        .distinct()
        .order_by(Project.name)
    )

    # Apply employer filter if specified
    if employer_id is not None:
        query = query.where(Project.on_behalf_of_id == employer_id)

    result = await session.execute(query)
    return list(result.scalars().all())
