"""MCP tools for querying data from Mosaic."""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from ..schemas.query_structured import StructuredQueryInput, StructuredQueryOutput
from ..server import AppContext, mcp
from ..services.query_service import QueryService

logger = logging.getLogger(__name__)


@mcp.tool()
async def query(
    input: StructuredQueryInput, ctx: Context[Any, AppContext, Any]
) -> StructuredQueryOutput:
    """
    Execute structured query with precise filters and aggregations.

    Uses a structured DSL instead of natural language for precise, type-safe queries.
    Supports complex filtering with 15 operators, relationship traversal, and
    aggregations with GROUP BY.

    See mosaic://docs/query-patterns for full documentation of the query language.

    Args:
        input: Structured query specification with filters and aggregations
        ctx: MCP context with app resources

    Returns:
        StructuredQueryOutput: Query results (entities or aggregations)

    Raises:
        ValueError: If query specification is invalid

    Examples:
        # Filter by date range
        {
          "entity_type": "work_session",
          "filters": [
            {"field": "date", "operator": "gte", "value": "this_week"}
          ]
        }

        # Relationship traversal
        {
          "entity_type": "work_session",
          "filters": [
            {"field": "project.name", "operator": "contains", "value": "Enterprise"}
          ]
        }

        # Aggregation with GROUP BY
        {
          "entity_type": "work_session",
          "filters": [
            {"field": "date", "operator": "gte", "value": "this_month"}
          ],
          "aggregation": {
            "function": "sum",
            "field": "duration_hours",
            "group_by": ["project.name"]
          }
        }
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = QueryService(session)

            # Execute structured query
            raw_result = await service.structured_query(
                entity_type=input.entity_type,
                filters=input.filters,
                aggregation=input.aggregation,
                limit=input.limit,
                offset=input.offset,
            )

            logger.info(
                f"Executed structured query: {input.entity_type} "
                f"with {len(input.filters)} filters"
            )

            return StructuredQueryOutput(**raw_result)
        except Exception as e:
            logger.error(f"Failed to execute structured query: {e}", exc_info=True)
            raise
