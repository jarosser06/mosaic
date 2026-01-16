"""Mosaic MCP server with FastMCP."""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from .config import settings
from .services.database import async_session_factory, close_db, engine, init_db
from .services.scheduler_service import SchedulerService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    Application context available to all MCP tools.

    Contains shared resources like database engine, session factory,
    scheduler, and settings.
    """

    engine: AsyncEngine
    session_factory: async_sessionmaker
    scheduler: SchedulerService
    settings: type[settings]


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncGenerator[AppContext, None]:
    """
    Lifespan context manager for MCP server.

    Handles startup (DB init, scheduler start) and shutdown (cleanup).

    Args:
        mcp: FastMCP server instance

    Yields:
        AppContext: Shared application context for tools
    """
    logger.info("Starting Mosaic MCP server...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start scheduler
    scheduler = SchedulerService()
    await scheduler.start()
    logger.info("Scheduler started")

    # Create and yield app context
    app_ctx = AppContext(
        engine=engine,
        session_factory=async_session_factory,
        scheduler=scheduler,
        settings=settings,
    )

    try:
        yield app_ctx
    finally:
        # Shutdown
        logger.info("Shutting down Mosaic MCP server...")

        # Stop scheduler
        await scheduler.stop()
        logger.info("Scheduler stopped")

        # Close database
        await close_db()
        logger.info("Database closed")


# Create FastMCP server with lifespan
mcp = FastMCP(
    name="mosaic",
    lifespan=lifespan,
)

# Import prompts to register them with the server
# This triggers the @mcp.prompt() decorators
from .prompts import prompt_registry  # noqa: E402, F401

# Import resources to register them with the server
# This triggers the @mcp.resource() decorators
from .resources import resource_handlers  # noqa: E402, F401

# Import tools to register them with the server
# This triggers the @mcp.tool() decorators
from .tools import (  # noqa: E402, F401
    logging_tools,
    notification_tools,
    query_tools,
    update_tools,
    user_tools,
)

logger.info("All tools, resources, and prompts registered")


def main() -> None:
    """Run the MCP server with stdio transport."""
    logger.info("Running Mosaic MCP server on stdio transport")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
