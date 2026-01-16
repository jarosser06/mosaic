"""MCP server fixtures for integration testing."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from src.mosaic.config import settings
from src.mosaic.server import AppContext
from src.mosaic.services.scheduler_service import SchedulerService


@pytest.fixture(scope="function")
async def test_app_context(
    test_engine: AsyncEngine,
    test_session_factory: async_sessionmaker,
) -> AppContext:
    """
    Create real AppContext for testing with test database.

    This is the REAL app context that tools receive via ctx.request_context.lifespan_context.
    It uses the test database instead of production database.

    NOTE: Scheduler is created but not started to avoid asyncio context issues in tests.
    """
    # Create scheduler but DON'T start it (to avoid asyncio teardown issues)
    scheduler = SchedulerService()

    app_ctx = AppContext(
        engine=test_engine,
        session_factory=test_session_factory,
        scheduler=scheduler,
        settings=settings,
    )

    yield app_ctx

    # No cleanup needed since scheduler was never started


@pytest.fixture(scope="function")
async def mcp_server(test_app_context: AppContext):
    """
    Get the production FastMCP server instance for testing.

    This uses the REAL MCP server from src.mosaic.server that already
    has all tools, resources, and prompts registered. Tests run against
    the test database via the test_app_context.

    NOTE: We use the production mcp instance because all decorators
    (@mcp.tool(), @mcp.resource(), @mcp.prompt()) are bound to it.
    """
    # Import the production mcp instance which already has everything registered
    from src.mosaic.server import mcp

    return mcp


@pytest.fixture(scope="function")
async def mcp_client(test_app_context: AppContext):
    """
    Create MCP client context for making tool calls.

    This provides a minimal Context object that matches the structure
    that real MCP tools receive:

        ctx.request_context.lifespan_context -> AppContext

    The key difference from production:
    - Uses test AppContext (with test database)
    - request_context is minimally mocked (only provides lifespan_context)
    """

    class TestContext:
        """Minimal Context implementation for testing."""

        def __init__(self, app_ctx: AppContext):
            # Create request_context with only lifespan_context attribute
            self.request_context = MagicMock()
            self.request_context.lifespan_context = app_ctx

    return TestContext(test_app_context)
