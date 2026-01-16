"""MCP tools for querying data from Mosaic."""

import logging

from mcp.server.fastmcp import Context

from ..schemas.query import QueryInput, QueryOutput
from ..server import mcp
from ..services.query_service import QueryService

logger = logging.getLogger(__name__)


@mcp.tool()
async def query(input: QueryInput, ctx: Context) -> QueryOutput:
    """
    Natural language query across all entities in Mosaic.

    Flexible search across work sessions, meetings, people, clients, projects,
    employers, notes, and reminders. Returns results grouped by entity type
    with a natural language summary.

    Supports filters like:
    - Time ranges (last week, this month, etc.)
    - Entity relationships (meetings with specific person, work on project)
    - Privacy levels (public, internal, private)
    - Text search (in descriptions, notes, names)
    - Status filters (active projects, completed reminders)

    Args:
        input: Natural language query string
        ctx: MCP context with app resources

    Returns:
        QueryOutput: Summary and list of matching entities (discriminated union)

    Raises:
        ValueError: If query is invalid or too complex
    """
    from ..services.query_parser import QueryParser
    from ..services.result_converter import ResultConverter
    from ..services.summary_generator import SummaryGenerator

    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            # 1. Parse the natural language query
            parser = QueryParser()
            parsed = parser.parse(input.query)

            # 2. Execute query with extracted filters
            service = QueryService(session)
            raw_results = await service.flexible_query(
                entity_types=parsed.entity_types,
                start_date=parsed.start_date,
                end_date=parsed.end_date,
                privacy_levels=parsed.privacy_levels,
                include_private=parsed.include_private,
                search_text=parsed.search_text,
                project_id=parsed.project_id,
                person_id=parsed.person_id,
                client_id=parsed.client_id,
                employer_id=parsed.employer_id,
                limit=parsed.limit,
            )

            # 3. Convert results to QueryResultEntity format
            converter = ResultConverter()
            results = converter.convert_results(raw_results)

            # 4. Generate natural language summary
            generator = SummaryGenerator()
            summary = generator.generate(results, include_private=parsed.include_private)

            logger.info(f"Executed query: '{input.query}' - Found {len(results)} results")

            return QueryOutput(
                summary=summary,
                results=results,
                total_count=len(results),
            )
        except Exception as e:
            logger.error(f"Failed to execute query: {e}", exc_info=True)
            raise
