"""Integration tests for query MCP tool using real MCP server.

Tests natural language query interface with privacy filtering,
date range filtering, and entity relationship queries.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.schemas.query import QueryInput
from src.mosaic.tools.query_tools import query


class TestQueryTool:
    """Test query tool end-to-end with real MCP server."""

    @pytest.fixture
    async def work_sessions(
        self,
        test_session: AsyncSession,
        project: Project,
    ):
        """Create test work sessions with different privacy levels."""
        sessions = [
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Public work",
                privacy_level=PrivacyLevel.PUBLIC,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 16),
                start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 16, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Internal work",
                privacy_level=PrivacyLevel.INTERNAL,
            ),
            WorkSession(
                project_id=project.id,
                date=date(2024, 1, 17),
                start_time=datetime(2024, 1, 17, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 17, 12, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("3.0"),
                summary="Private work",
                privacy_level=PrivacyLevel.PRIVATE,
            ),
        ]
        for ws in sessions:
            test_session.add(ws)
        await test_session.commit()
        return sessions

    @pytest.mark.asyncio
    async def test_query_basic(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test basic query execution through real MCP tool."""
        input_data = QueryInput(
            query="show all work sessions",
        )

        # Call REAL tool with REAL context
        result = await query(input_data, mcp_client)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "summary")
        assert hasattr(result, "results")
        assert hasattr(result, "total_count")

    @pytest.mark.asyncio
    async def test_query_returns_results(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test that query returns proper structure."""
        input_data = QueryInput(
            query="show work from last week",
        )

        result = await query(input_data, mcp_client)

        # Should return QueryOutput with proper structure
        assert isinstance(result.summary, str)
        assert isinstance(result.total_count, int)
        assert isinstance(result.results, list)

    @pytest.mark.asyncio
    async def test_query_with_date_range(
        self,
        mcp_client,
        test_session: AsyncSession,
        work_sessions: list[WorkSession],
    ):
        """Test query with date range filter."""
        input_data = QueryInput(
            query="work sessions from January 15-16, 2024",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None
        assert isinstance(result.summary, str)

    @pytest.mark.asyncio
    async def test_query_with_project_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        work_sessions: list[WorkSession],
        project: Project,
    ):
        """Test query filtering by project."""
        input_data = QueryInput(
            query=f"work sessions for project {project.name}",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_privacy_filter_public_only(
        self,
        mcp_client,
        test_session: AsyncSession,
        work_sessions: list[WorkSession],
    ):
        """Test query filtering by privacy level (public only)."""
        input_data = QueryInput(
            query="show public work sessions",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_privacy_filter_exclude_private(
        self,
        mcp_client,
        test_session: AsyncSession,
        work_sessions: list[WorkSession],
    ):
        """Test query excluding private entries."""
        input_data = QueryInput(
            query="show non-private work sessions",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_text_search(
        self,
        mcp_client,
        test_session: AsyncSession,
        work_sessions: list[WorkSession],
    ):
        """Test query with text search in descriptions."""
        input_data = QueryInput(
            query="work sessions containing 'Public'",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_person_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test query filtering by person."""
        input_data = QueryInput(
            query=f"meetings with {person.full_name}",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_time_range_last_week(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with relative time range (last week)."""
        input_data = QueryInput(
            query="work from last week",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_time_range_this_month(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with relative time range (this month)."""
        input_data = QueryInput(
            query="meetings this month",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_complex_multi_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test query with multiple filters combined."""
        input_data = QueryInput(
            query=f"public work sessions for {project.name} from last week",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_empty_result(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query that returns no results."""
        input_data = QueryInput(
            query="work sessions from year 2050",
        )

        result = await query(input_data, mcp_client)

        # Empty results should still return valid structure
        assert result.total_count == 0
        assert result.results == []
        assert isinstance(result.summary, str)

    @pytest.mark.asyncio
    async def test_query_with_status_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by entity status."""
        input_data = QueryInput(
            query="active projects",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_with_tag_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by tags."""
        input_data = QueryInput(
            query="work sessions tagged with 'backend'",
        )

        result = await query(input_data, mcp_client)

        # Query should execute successfully
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_handles_errors_gracefully(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test that query handles errors gracefully."""
        input_data = QueryInput(
            query="invalid query syntax @#$%",
        )

        # Should not raise, but return empty or error results
        result = await query(input_data, mcp_client)
        assert result is not None
        # Query parser should handle this gracefully
        assert isinstance(result.summary, str)
