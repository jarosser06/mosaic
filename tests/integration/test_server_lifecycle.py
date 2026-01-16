"""Integration tests for MCP server lifecycle (startup/shutdown).

Tests server initialization, database connections, scheduler startup,
and proper cleanup on shutdown.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mosaic.server import AppContext, lifespan, mcp


class TestServerLifecycle:
    """Test MCP server startup and shutdown."""

    @pytest.mark.asyncio
    async def test_server_startup_initializes_database(self):
        """Test that server startup initializes database."""
        with patch("src.mosaic.server.init_db") as mock_init_db:
            mock_init_db.return_value = AsyncMock()

            with patch(
                "src.mosaic.services.scheduler_service.SchedulerService.start"
            ) as mock_start:
                mock_start.return_value = AsyncMock()

                async with lifespan(mcp) as app_ctx:
                    # Verify init_db was called
                    mock_init_db.assert_called_once()
                    assert isinstance(app_ctx, AppContext)

    @pytest.mark.asyncio
    async def test_server_startup_initializes_scheduler(self):
        """Test that server startup initializes scheduler."""
        with patch("src.mosaic.server.init_db") as mock_init_db:
            mock_init_db.return_value = AsyncMock()

            with patch(
                "src.mosaic.services.scheduler_service.SchedulerService.start"
            ) as mock_start:
                mock_start.return_value = AsyncMock()

                async with lifespan(mcp) as app_ctx:
                    # Verify scheduler start was called
                    mock_start.assert_called_once()
                    assert app_ctx.scheduler is not None

    @pytest.mark.asyncio
    async def test_server_shutdown_stops_scheduler(self):
        """Test that server shutdown stops scheduler gracefully."""
        with patch("src.mosaic.server.init_db") as mock_init_db:
            mock_init_db.return_value = AsyncMock()

            # Patch SchedulerService where it's used (in server.py), not where it's defined
            with patch("src.mosaic.server.SchedulerService") as MockSchedulerClass:
                # Create a mock instance with start and stop as AsyncMocks
                mock_instance = MagicMock()
                mock_instance.start = AsyncMock()
                mock_instance.stop = AsyncMock()

                # Make the class constructor return our mock instance
                MockSchedulerClass.return_value = mock_instance

                with patch("src.mosaic.server.close_db") as mock_close_db:
                    mock_close_db.return_value = AsyncMock()

                    async with lifespan(mcp):
                        pass  # Exit context to trigger shutdown

                    # Verify scheduler stop was called
                    mock_instance.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_shutdown_closes_database(self):
        """Test that server shutdown closes database connections."""
        with patch("src.mosaic.server.init_db") as mock_init_db:
            mock_init_db.return_value = AsyncMock()

            with patch(
                "src.mosaic.services.scheduler_service.SchedulerService.start"
            ) as mock_start:
                mock_start.return_value = AsyncMock()

                with patch(
                    "src.mosaic.services.scheduler_service.SchedulerService.stop"
                ) as mock_stop:
                    mock_stop.return_value = AsyncMock()

                    with patch("src.mosaic.server.close_db") as mock_close_db:
                        mock_close_db.return_value = AsyncMock()

                        async with lifespan(mcp):
                            pass  # Exit context to trigger shutdown

                        # Verify close_db was called
                        mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_app_context_has_required_fields(self):
        """Test that AppContext has all required fields."""
        with patch("src.mosaic.server.init_db") as mock_init_db:
            mock_init_db.return_value = AsyncMock()

            with patch(
                "src.mosaic.services.scheduler_service.SchedulerService.start"
            ) as mock_start:
                mock_start.return_value = AsyncMock()

                async with lifespan(mcp) as app_ctx:
                    # Verify all fields are present
                    assert hasattr(app_ctx, "engine")
                    assert hasattr(app_ctx, "session_factory")
                    assert hasattr(app_ctx, "scheduler")
                    assert hasattr(app_ctx, "settings")

                    # Verify types
                    assert app_ctx.engine is not None
                    assert app_ctx.session_factory is not None
                    assert app_ctx.scheduler is not None
                    assert app_ctx.settings is not None
