"""MCP tools for timecard generation."""

import logging
from decimal import Decimal
from typing import Any

from mcp.server.fastmcp import Context

from ..repositories.project_repository import ProjectRepository
from ..schemas.timecard import TimecardEntry, TimecardInput, TimecardOutput
from ..server import AppContext, mcp
from ..services.work_session_service import WorkSessionService

logger = logging.getLogger(__name__)


@mcp.tool()
async def generate_timecard(
    input: TimecardInput, ctx: Context[Any, AppContext, TimecardInput]
) -> TimecardOutput:
    """
    Generate a timecard for a date range with aggregated work sessions.

    Groups work sessions by date and project, aggregating hours and summaries.
    Half-hour rounding is preserved from individual work sessions.

    Supports filters for:
    - Privacy level (include/exclude PRIVATE sessions)
    - Specific project (filter to one project)

    Args:
        input: Timecard parameters (date range, filters)
        ctx: MCP context with app resources

    Returns:
        TimecardOutput: Aggregated timecard entries with totals

    Raises:
        ValueError: If date range is invalid (end_date before start_date)
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            # 1. Call work session service to generate timecard data
            service = WorkSessionService(session)
            timecard_data = await service.generate_timecard(
                start_date=input.start_date,
                end_date=input.end_date,
                include_private=input.include_private,
                project_id=input.project_id,
            )

            # 2. Fetch project names for all project_ids in results
            project_ids = {row["project_id"] for row in timecard_data}
            project_repo = ProjectRepository(session)
            project_names: dict[int, str] = {}

            for project_id in project_ids:
                project = await project_repo.get_by_id(project_id)
                if project:
                    project_names[project_id] = project.name
                else:
                    # Fallback if project not found (shouldn't happen)
                    project_names[project_id] = f"Project {project_id}"

            # 3. Convert dict results to TimecardEntry models
            entries: list[TimecardEntry] = []
            for row in timecard_data:
                entry = TimecardEntry(
                    date=row["date"],
                    project_id=row["project_id"],
                    project_name=project_names[row["project_id"]],
                    total_hours=row["total_hours"],
                    summary=row["summary"] if row["summary"] else None,
                )
                entries.append(entry)

            # 4. Calculate total hours across all entries
            total_hours = sum(
                (entry.total_hours for entry in entries),
                start=Decimal("0.0"),
            )

            # 5. Determine if privacy filter was applied
            privacy_filter_applied = not input.include_private

            logger.info(
                f"Generated timecard: {input.start_date} to {input.end_date}, "
                f"{len(entries)} entries, {total_hours} total hours"
            )

            return TimecardOutput(
                start_date=input.start_date,
                end_date=input.end_date,
                entries=entries,
                total_hours=total_hours,
                project_filter=input.project_id,
                privacy_filter_applied=privacy_filter_applied,
            )

        except Exception as e:
            logger.error(f"Failed to generate timecard: {e}", exc_info=True)
            raise
