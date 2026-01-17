"""Integration tests for generate_timecard MCP tool.

Tests end-to-end timecard generation through the MCP tool,
including aggregation, privacy filtering, and date range validation.

NOTE: These tests follow TDD - they will FAIL until the tool is implemented.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.project import Project
from src.mosaic.schemas.timecard import TimecardInput
from src.mosaic.tools.timecard_tools import generate_timecard


class TestGenerateTimecardTool:
    """Test generate_timecard tool with real MCP server."""

    @pytest.fixture
    async def project_alpha(
        self,
        test_session: AsyncSession,
        employer,
        client,
    ) -> Project:
        """Create Project Alpha for testing."""
        from src.mosaic.models.project import ProjectStatus

        project = Project(
            name="Project Alpha",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add(project)
        await test_session.commit()
        await test_session.refresh(project)
        return project

    @pytest.fixture
    async def project_beta(
        self,
        test_session: AsyncSession,
        employer,
        client,
    ) -> Project:
        """Create Project Beta for testing."""
        from src.mosaic.models.project import ProjectStatus

        project = Project(
            name="Project Beta",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add(project)
        await test_session.commit()
        await test_session.refresh(project)
        return project

    async def _create_work_session(
        self,
        test_session: AsyncSession,
        project_id: int,
        start_time: datetime,
        end_time: datetime,
        summary: str | None = None,
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
    ):
        """Helper to create a work session directly in database."""
        from src.mosaic.models.work_session import WorkSession
        from src.mosaic.services.time_utils import round_to_half_hour

        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        duration_hours = round_to_half_hour(duration_minutes)

        session = WorkSession(
            project_id=project_id,
            date=start_time.date(),
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            summary=summary,
            privacy_level=privacy_level,
        )
        test_session.add(session)
        await test_session.commit()
        return session

    @pytest.mark.asyncio
    async def test_generate_basic_timecard(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test generating a basic timecard with one work session."""
        # Create work session
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
            summary="Full day of work",
        )

        # Generate timecard
        input_data = TimecardInput(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
            include_private=True,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Verify result
        assert result.start_date == date(2024, 1, 15)
        assert result.end_date == date(2024, 1, 15)
        assert len(result.entries) == 1
        assert result.entries[0].date == date(2024, 1, 15)
        assert result.entries[0].project_id == project_alpha.id
        assert result.entries[0].project_name == "Project Alpha"
        assert result.entries[0].total_hours == Decimal("8.0")
        assert result.entries[0].summary == "Full day of work"
        assert result.total_hours == Decimal("8.0")
        assert result.privacy_filter_applied is False

    @pytest.mark.asyncio
    async def test_timecard_aggregates_multiple_sessions_same_day(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard aggregates multiple sessions on same project/date."""
        work_date = date(2024, 1, 15)

        # Create 3 sessions on same day, same project
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),  # 1.5h
            summary="Morning: Feature development",
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 13, 15, tzinfo=timezone.utc),  # 2.5h
            summary="Midday: Code review",
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 17, 45, tzinfo=timezone.utc),  # 4.0h
            summary="Afternoon: Bug fixes",
        )

        # Generate timecard
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should have 1 entry with aggregated hours
        assert len(result.entries) == 1
        assert result.entries[0].total_hours == Decimal("8.0")  # 1.5 + 2.5 + 4.0
        assert result.total_hours == Decimal("8.0")
        # Summary should contain all three summaries
        summary = result.entries[0].summary
        assert summary is not None
        assert "Morning: Feature development" in summary
        assert "Midday: Code review" in summary
        assert "Afternoon: Bug fixes" in summary

    @pytest.mark.asyncio
    async def test_timecard_multiple_projects_same_day(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
        project_beta: Project,
    ):
        """Test timecard with multiple projects on same day creates separate entries."""
        work_date = date(2024, 1, 15)

        # Create sessions for both projects on same day
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            summary="Alpha work",
        )
        await self._create_work_session(
            test_session,
            project_beta.id,
            datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
            summary="Beta work",
        )

        # Generate timecard
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should have 2 entries (one per project)
        assert len(result.entries) == 2
        assert result.total_hours == Decimal("7.0")  # 3.0 + 4.0

        # Verify both projects are present
        project_ids = {entry.project_id for entry in result.entries}
        assert project_alpha.id in project_ids
        assert project_beta.id in project_ids

        # Find entries by project
        alpha_entry = next(e for e in result.entries if e.project_id == project_alpha.id)
        beta_entry = next(e for e in result.entries if e.project_id == project_beta.id)

        assert alpha_entry.total_hours == Decimal("3.0")
        assert alpha_entry.project_name == "Project Alpha"
        assert beta_entry.total_hours == Decimal("4.0")
        assert beta_entry.project_name == "Project Beta"

    @pytest.mark.asyncio
    async def test_timecard_privacy_filter_excludes_private(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard excludes private sessions when include_private=False."""
        work_date = date(2024, 1, 15)

        # Create sessions with different privacy levels
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PUBLIC,
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PRIVATE,
        )

        # Generate timecard excluding private
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
            include_private=False,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should only include PUBLIC session (2.0 hours)
        assert len(result.entries) == 1
        assert result.entries[0].total_hours == Decimal("2.0")
        assert result.total_hours == Decimal("2.0")
        assert result.privacy_filter_applied is True

    @pytest.mark.asyncio
    async def test_timecard_privacy_filter_includes_private(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard includes private sessions when include_private=True."""
        work_date = date(2024, 1, 15)

        # Create sessions with different privacy levels
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PUBLIC,
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PRIVATE,
        )

        # Generate timecard including private
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
            include_private=True,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should include both sessions (4.0 hours total)
        assert len(result.entries) == 1
        assert result.entries[0].total_hours == Decimal("4.0")
        assert result.total_hours == Decimal("4.0")
        assert result.privacy_filter_applied is False

    @pytest.mark.asyncio
    async def test_timecard_date_range_filtering(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard respects date range boundaries."""
        # Create sessions across multiple weeks
        dates = [date(2024, 1, 10), date(2024, 1, 15), date(2024, 1, 20)]
        for d in dates:
            await self._create_work_session(
                test_session,
                project_alpha.id,
                datetime.combine(d, datetime.min.time()).replace(hour=9, tzinfo=timezone.utc),
                datetime.combine(d, datetime.min.time()).replace(hour=17, tzinfo=timezone.utc),
            )

        # Generate timecard for Jan 12-18 (should only include Jan 15)
        input_data = TimecardInput(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18),
        )

        result = await generate_timecard(input_data, mcp_client)

        assert len(result.entries) == 1
        assert result.entries[0].date == date(2024, 1, 15)
        assert result.total_hours == Decimal("8.0")

    @pytest.mark.asyncio
    async def test_timecard_project_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
        project_beta: Project,
    ):
        """Test timecard can filter by specific project."""
        work_date = date(2024, 1, 15)

        # Create sessions for both projects
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )
        await self._create_work_session(
            test_session,
            project_beta.id,
            datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        )

        # Generate timecard for Project Alpha only
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
            project_id=project_alpha.id,
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should only include Project Alpha
        assert len(result.entries) == 1
        assert result.entries[0].project_id == project_alpha.id
        assert result.entries[0].project_name == "Project Alpha"
        assert result.total_hours == Decimal("3.0")
        assert result.project_filter == project_alpha.id

    @pytest.mark.asyncio
    async def test_timecard_empty_range(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test timecard returns empty entries when no sessions in range."""
        input_data = TimecardInput(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        result = await generate_timecard(input_data, mcp_client)

        assert result.entries == []
        assert result.total_hours == Decimal("0.0")

    @pytest.mark.asyncio
    async def test_timecard_invalid_date_range(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test timecard raises validation error for invalid date range."""
        with pytest.raises(ValidationError, match="end_date must be on or after start_date"):
            TimecardInput(
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),
            )

    @pytest.mark.asyncio
    async def test_timecard_multiple_days_same_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard creates separate entries for same project on different days."""
        # Create sessions for 3 consecutive days
        for i in range(3):
            work_date = date(2024, 1, 15 + i)
            await self._create_work_session(
                test_session,
                project_alpha.id,
                datetime.combine(work_date, datetime.min.time()).replace(
                    hour=9, tzinfo=timezone.utc
                ),
                datetime.combine(work_date, datetime.min.time()).replace(
                    hour=17, tzinfo=timezone.utc
                ),
                summary=f"Day {i+1} work",
            )

        # Generate timecard
        input_data = TimecardInput(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 17),
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should have 3 entries (one per day)
        assert len(result.entries) == 3
        assert result.total_hours == Decimal("24.0")  # 8.0 * 3

        # Verify dates are correct
        dates = {entry.date for entry in result.entries}
        assert dates == {date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17)}

        # Each entry should be 8 hours
        for entry in result.entries:
            assert entry.total_hours == Decimal("8.0")
            assert entry.project_id == project_alpha.id

    @pytest.mark.asyncio
    async def test_timecard_half_hour_rounding_preserved(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard preserves half-hour rounding from work sessions."""
        work_date = date(2024, 1, 15)

        # Create session with odd duration that rounds to half-hour
        # 2:15 -> 2.5 hours
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 11, 15, tzinfo=timezone.utc),
        )

        # Generate timecard
        input_data = TimecardInput(
            start_date=work_date,
            end_date=work_date,
        )

        result = await generate_timecard(input_data, mcp_client)

        assert len(result.entries) == 1
        assert result.entries[0].total_hours == Decimal("2.5")
        assert result.total_hours == Decimal("2.5")

    @pytest.mark.asyncio
    async def test_timecard_entries_sorted_by_date_then_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project_alpha: Project,
        project_beta: Project,
    ):
        """Test timecard entries are sorted by date, then project_id."""
        # Create sessions in mixed order
        await self._create_work_session(
            test_session,
            project_beta.id,
            datetime(2024, 1, 17, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 17, 12, 0, tzinfo=timezone.utc),
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )
        await self._create_work_session(
            test_session,
            project_alpha.id,
            datetime(2024, 1, 17, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 17, 16, 0, tzinfo=timezone.utc),
        )
        await self._create_work_session(
            test_session,
            project_beta.id,
            datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 16, 0, tzinfo=timezone.utc),
        )

        # Generate timecard
        input_data = TimecardInput(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 17),
        )

        result = await generate_timecard(input_data, mcp_client)

        # Should have 4 entries sorted by date, then project_id
        assert len(result.entries) == 4

        # Verify sort order
        expected_order = [
            (date(2024, 1, 15), project_alpha.id),
            (date(2024, 1, 15), project_beta.id),
            (date(2024, 1, 17), project_alpha.id),
            (date(2024, 1, 17), project_beta.id),
        ]

        actual_order = [(e.date, e.project_id) for e in result.entries]
        assert actual_order == expected_order
