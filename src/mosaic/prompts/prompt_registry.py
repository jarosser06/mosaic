"""MCP prompt registration with decorators.

Wraps prompt handler functions with @mcp.prompt() decorators to register
them with the FastMCP server. Each prompt returns a list of PromptMessage
objects with TextContent.
"""

from datetime import date
from typing import Any, Optional

from mcp.server.fastmcp import Context
from mcp.types import PromptMessage, TextContent

from ..server import AppContext, mcp
from .prompt_handlers import (
    generate_add_person_prompt,
    generate_find_gaps_prompt,
    generate_generate_timecard_prompt,
    generate_log_meeting_prompt,
    generate_log_work_prompt,
    generate_reminder_review_prompt,
    generate_search_context_prompt,
    generate_weekly_review_prompt,
)


@mcp.prompt(
    name="log-work",
    description="Generate prompt for logging work sessions with active projects context",
)
async def log_work_prompt(ctx: Context[Any, AppContext, Any]) -> list[PromptMessage]:
    """
    Prompt for logging work sessions.

    Shows active projects grouped by employer to help with work logging.

    Args:
        ctx: MCP context with app resources

    Returns:
        list[PromptMessage]: Prompt messages with active projects context
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_log_work_prompt(session)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="log-meeting",
    description="Generate prompt for logging meetings with people and projects context",
)
async def log_meeting_prompt(ctx: Context[Any, AppContext, Any]) -> list[PromptMessage]:
    """
    Prompt for logging meetings.

    Shows known people (highlighting stakeholders) and active projects.

    Args:
        ctx: MCP context with app resources

    Returns:
        list[PromptMessage]: Prompt messages with people and projects context
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_log_meeting_prompt(session)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="add-person",
    description="Generate prompt for adding people with duplicate prevention context",
)
async def add_person_prompt(ctx: Context[Any, AppContext, Any]) -> list[PromptMessage]:
    """
    Prompt for adding new people.

    Shows existing people to help avoid creating duplicates.

    Args:
        ctx: MCP context with app resources

    Returns:
        list[PromptMessage]: Prompt messages with existing people list
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_add_person_prompt(session)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="generate-timecard",
    description="Generate prompt for timecard generation with employer and date context",
)
async def generate_timecard_prompt(
    ctx: Context[Any, AppContext, Any],
    employer_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[PromptMessage]:
    """
    Prompt for timecard generation.

    Provides different guidance based on which parameters are provided.

    Args:
        ctx: MCP context with app resources
        employer_name: Optional employer filter
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        list[PromptMessage]: Prompt messages with employer and date context
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_generate_timecard_prompt(
            session,
            employer_name=employer_name,
            start_date=start_date,
            end_date=end_date,
        )
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="weekly-review", description="Generate prompt for weekly review with activity metrics"
)
async def weekly_review_prompt(
    ctx: Context[Any, AppContext, Any],
    week_start: Optional[date] = None,
) -> list[PromptMessage]:
    """
    Prompt for weekly review.

    Shows summary of work hours and meetings for the specified week.

    Args:
        ctx: MCP context with app resources
        week_start: Optional week start date (defaults to current week)

    Returns:
        list[PromptMessage]: Prompt messages with weekly metrics
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_weekly_review_prompt(session, week_start=week_start)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(name="find-gaps", description="Generate prompt for gap analysis in logged work time")
async def find_gaps_prompt(
    ctx: Context[Any, AppContext, Any],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[PromptMessage]:
    """
    Prompt for gap analysis.

    Identifies days with missing or incomplete work logs.

    Args:
        ctx: MCP context with app resources
        start_date: Optional start date (defaults to current week)
        end_date: Optional end date (defaults to current week)

    Returns:
        list[PromptMessage]: Prompt messages with gap analysis
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_find_gaps_prompt(
            session,
            start_date=start_date,
            end_date=end_date,
        )
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="search-context", description="Generate prompt for context search with query guidance"
)
async def search_context_prompt(
    ctx: Context[Any, AppContext, Any], query: str
) -> list[PromptMessage]:
    """
    Prompt for context search.

    Provides search suggestions and available filters.

    Args:
        ctx: MCP context with app resources
        query: Search query (REQUIRED)

    Returns:
        list[PromptMessage]: Prompt messages with search guidance

    Raises:
        ValueError: If query is not provided
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_search_context_prompt(session, query=query)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]


@mcp.prompt(
    name="reminder-review", description="Generate prompt for reminder review with pending reminders"
)
async def reminder_review_prompt(ctx: Context[Any, AppContext, Any]) -> list[PromptMessage]:
    """
    Prompt for reminder review.

    Lists all pending reminders sorted by due time.

    Args:
        ctx: MCP context with app resources

    Returns:
        list[PromptMessage]: Prompt messages with pending reminders
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        content = await generate_reminder_review_prompt(session)
        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=content),
            )
        ]
