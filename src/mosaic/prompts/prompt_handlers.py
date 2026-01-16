"""MCP prompt handler functions.

Generates dynamic, context-aware prompts for Claude based on current system state.
Each handler queries the database to provide relevant context and guidance.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mosaic.models.base import ProjectStatus
from mosaic.models.employer import Employer
from mosaic.models.meeting import Meeting
from mosaic.models.person import Person
from mosaic.models.project import Project
from mosaic.models.reminder import Reminder
from mosaic.models.work_session import WorkSession


async def generate_log_work_prompt(session: AsyncSession) -> str:
    """
    Generate prompt for log-work with active projects context.

    Shows user's active projects grouped by employer to help with work logging.

    Args:
        session: Database session

    Returns:
        str: Prompt content with active projects listed
    """
    # Fetch active projects with employer relationship
    result = await session.execute(
        select(Project)
        .where(Project.status == ProjectStatus.ACTIVE)
        .options(selectinload(Project.employer))
        .order_by(Project.on_behalf_of_id, Project.name)
    )
    projects = list(result.scalars().all())

    if not projects:
        return (
            "You don't have any active projects yet. " "Create a project first to track your work."
        )

    # Group projects by employer
    employer_groups: dict[str, list[Project]] = {}
    for project in projects:
        employer_name = project.employer.name if project.employer else "Unknown"
        if employer_name not in employer_groups:
            employer_groups[employer_name] = []
        employer_groups[employer_name].append(project)

    # Build prompt
    lines = ["Log work session for one of your active projects:\n"]

    for employer_name, emp_projects in employer_groups.items():
        lines.append(f"\n**{employer_name}:**")
        for proj in emp_projects:
            lines.append(f"  - {proj.name}")

    return "\n".join(lines)


async def generate_log_meeting_prompt(session: AsyncSession) -> str:
    """
    Generate prompt for log-meeting with people and projects context.

    Shows known people (highlighting stakeholders) and active projects
    to help with meeting logging.

    Args:
        session: Database session

    Returns:
        str: Prompt content with people and projects listed
    """
    # Fetch people
    people_result = await session.execute(select(Person).order_by(Person.full_name))
    people = list(people_result.scalars().all())

    # Fetch active projects
    projects_result = await session.execute(
        select(Project).where(Project.status == ProjectStatus.ACTIVE).order_by(Project.name)
    )
    projects = list(projects_result.scalars().all())

    lines = ["Log a meeting with participants and optional project association:\n"]

    # Add people section
    if people:
        lines.append("\n**Known People:**")
        stakeholders = [p for p in people if p.is_stakeholder]
        regular = [p for p in people if not p.is_stakeholder]

        if stakeholders:
            lines.append("\n*Stakeholders:*")
            for person in stakeholders:
                lines.append(f"  - {person.full_name} ({person.email})")

        if regular:
            lines.append("\n*Other:*")
            for person in regular:
                lines.append(f"  - {person.full_name} ({person.email})")
    else:
        lines.append("\nNo people in database yet. Add attendees when logging the meeting.")

    # Add projects section
    if projects:
        lines.append("\n**Active Projects (for association):**")
        for proj in projects:
            lines.append(f"  - {proj.name}")
    else:
        lines.append("\nNo active projects.")

    return "\n".join(lines)


async def generate_add_person_prompt(session: AsyncSession) -> str:
    """
    Generate prompt for add-person with duplicate prevention context.

    Shows existing people to help avoid creating duplicates.

    Args:
        session: Database session

    Returns:
        str: Prompt content with existing people listed
    """
    result = await session.execute(select(Person).order_by(Person.full_name))
    people = list(result.scalars().all())

    if not people:
        return "Add your first person to the database. No existing people to check for duplicates."

    lines = [
        "Add a new person. Check for duplicates before creating:\n",
        "\n**Existing People:**",
    ]

    for person in people:
        lines.append(f"  - {person.full_name} ({person.email})")

    lines.append("\nPlease verify this person doesn't already exist to avoid duplicates.")

    return "\n".join(lines)


async def generate_generate_timecard_prompt(
    session: AsyncSession,
    employer_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> str:
    """
    Generate prompt for timecard generation with employer and date context.

    Provides different guidance based on which parameters are provided.

    Args:
        session: Database session
        employer_name: Optional employer filter
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        str: Prompt content with context and guidance
    """
    if employer_name is None and start_date is None and end_date is None:
        # No args - show employer options
        result = await session.execute(
            select(Employer).order_by(Employer.is_current.desc(), Employer.name)
        )
        employers = list(result.scalars().all())

        if not employers:
            return "No employers found. Create an employer first to generate timecards."

        lines = ["Generate timecard for an employer:\n", "\n**Available Employers:**"]
        for emp in employers:
            current = " (current)" if emp.is_current else ""
            lines.append(f"  - {emp.name}{current}")

        return "\n".join(lines)

    if employer_name and start_date is None and end_date is None:
        # Employer specified, need date range
        return (
            f"Generate timecard for {employer_name}. "
            "Specify a date range (start_date and end_date) or use current week."
        )

    # All args specified - check for work sessions
    if employer_name and start_date and end_date:
        # Find employer
        employer_result = await session.execute(
            select(Employer).where(Employer.name == employer_name)
        )
        employer = employer_result.scalar_one_or_none()

        if not employer:
            return f"Employer '{employer_name}' not found."

        # Count work sessions in range for this employer
        count_result = await session.execute(
            select(func.count(WorkSession.id))
            .join(Project)
            .where(Project.on_behalf_of_id == employer.id)
            .where(WorkSession.date >= start_date)
            .where(WorkSession.date <= end_date)
        )
        count = count_result.scalar() or 0

        if count == 0:
            return (
                f"Generate timecard for {employer_name} from {start_date} to {end_date}. "
                f"Warning: No work sessions found in this date range."
            )

        return (
            f"Generate timecard for {employer_name} from {start_date} to {end_date}. "
            f"Found {count} work session(s) to include."
        )

    return "Invalid parameter combination for timecard generation."


async def generate_weekly_review_prompt(
    session: AsyncSession,
    week_start: Optional[date] = None,
) -> str:
    """
    Generate prompt for weekly review with activity metrics.

    Shows summary of work hours and meetings for the specified week.

    Args:
        session: Database session
        week_start: Optional week start date (defaults to current week)

    Returns:
        str: Prompt content with weekly metrics
    """
    if week_start is None:
        # Default to current week (Monday)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    # Count work sessions and sum hours
    ws_result = await session.execute(
        select(func.count(WorkSession.id), func.sum(WorkSession.duration_hours))
        .where(WorkSession.date >= week_start)
        .where(WorkSession.date <= week_end)
    )
    ws_count, total_hours = ws_result.one()
    ws_count = ws_count or 0
    total_hours = total_hours or 0

    # Count meetings (using start_time's date part)
    week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
    week_end_dt = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=timezone.utc)

    meeting_result = await session.execute(
        select(func.count(Meeting.id))
        .where(Meeting.start_time >= week_start_dt)
        .where(Meeting.start_time <= week_end_dt)
    )
    meeting_count = meeting_result.scalar() or 0

    lines = [
        f"Weekly review for week starting {week_start}:\n",
        "**Summary:**",
        f"  - Work sessions: {ws_count}",
        f"  - Total hours: {total_hours}",
        f"  - Meetings: {meeting_count}",
    ]

    return "\n".join(lines)


async def generate_find_gaps_prompt(
    session: AsyncSession,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> str:
    """
    Generate prompt for gap analysis in logged work time.

    Identifies days with missing or incomplete work logs.

    Args:
        session: Database session
        start_date: Optional start date (defaults to current week)
        end_date: Optional end date (defaults to current week)

    Returns:
        str: Prompt content with gap analysis
    """
    if start_date is None or end_date is None:
        # Default to current week
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    # Find all days with work sessions
    result = await session.execute(
        select(WorkSession.date)
        .where(WorkSession.date >= start_date)
        .where(WorkSession.date <= end_date)
        .distinct()
    )
    logged_days = {row[0] for row in result.all()}

    # Generate list of all days in range
    all_days = []
    current = start_date
    while current <= end_date:
        all_days.append(current)
        current += timedelta(days=1)

    # Find gaps (weekdays without logs)
    gaps = []
    for day in all_days:
        # Skip weekends (Saturday=5, Sunday=6)
        if day.weekday() < 5 and day not in logged_days:
            gaps.append(day)

    lines = [
        f"Gap analysis for {start_date} to {end_date}:\n",
    ]

    if gaps:
        lines.append(f"**Missing work logs on {len(gaps)} workday(s):**")
        for gap_day in gaps:
            day_name = gap_day.strftime("%A")
            lines.append(f"  - {gap_day} ({day_name})")
    else:
        lines.append("No gaps found - all workdays have logged time.")

    return "\n".join(lines)


async def generate_search_context_prompt(
    session: AsyncSession,
    query: Optional[str] = None,
) -> str:
    """
    Generate prompt for context search with query guidance.

    Provides search suggestions and available filters.

    Args:
        session: Database session
        query: Search query (REQUIRED)

    Returns:
        str: Prompt content with search guidance

    Raises:
        ValueError: If query is not provided
    """
    if query is None:
        raise ValueError("query is required for search-context prompt")

    lines = [
        f"Search for context matching: '{query}'\n",
        "**Search tips:**",
        "  - Search spans work sessions, meetings, notes, and people",
        "  - Use filters to refine results (project, date range, entity type)",
        "  - Results are ranked by relevance",
    ]

    return "\n".join(lines)


async def generate_reminder_review_prompt(session: AsyncSession) -> str:
    """
    Generate prompt for reminder review with pending reminders.

    Lists all pending reminders sorted by due time.

    Args:
        session: Database session

    Returns:
        str: Prompt content with pending reminders
    """
    result = await session.execute(
        select(Reminder)
        .where(Reminder.is_completed == False)  # noqa: E712
        .order_by(Reminder.reminder_time)
    )
    reminders = list(result.scalars().all())

    if not reminders:
        return "No pending reminders. You're all caught up!"

    lines = [
        f"You have {len(reminders)} pending reminder(s):\n",
    ]

    now = datetime.now(timezone.utc)
    for reminder in reminders:
        due_str = reminder.reminder_time.strftime("%Y-%m-%d %H:%M")
        overdue = " (OVERDUE)" if reminder.reminder_time < now else ""
        lines.append(f"  - {due_str}: {reminder.message}{overdue}")

    return "\n".join(lines)
