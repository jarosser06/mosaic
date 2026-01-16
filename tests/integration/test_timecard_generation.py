"""Integration tests for timecard generation with aggregation.

CRITICAL: These tests verify timecard generation with multiple sessions
merged by project and date.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project
from src.mosaic.services.work_session_service import WorkSessionService


class TestTimecardGeneration:
    """Test timecard generation with aggregation."""

    @pytest.fixture
    async def work_session_service(self, session: AsyncSession) -> WorkSessionService:
        """Create work session service."""
        return WorkSessionService(session)

    @pytest.fixture
    async def project_alpha(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ) -> Project:
        """Create Project Alpha."""
        project = Project(
            name="Project Alpha",
            on_behalf_of_id=employer.id,
            client_id=client.id,
        )
        session.add(project)
        await session.flush()
        await session.refresh(project)
        return project

    @pytest.fixture
    async def project_beta(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ) -> Project:
        """Create Project Beta."""
        project = Project(
            name="Project Beta",
            on_behalf_of_id=employer.id,
            client_id=client.id,
        )
        session.add(project)
        await session.flush()
        await session.refresh(project)
        return project

    async def test_timecard_single_session_per_day(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard with single session per day."""
        # Create work sessions for 3 consecutive days
        start_date = date(2024, 1, 15)
        for i in range(3):
            work_date = date(2024, 1, 15 + i)
            await work_session_service.create_work_session(
                project_id=project_alpha.id,
                start_time=datetime.combine(work_date, datetime.min.time()).replace(
                    hour=9, tzinfo=timezone.utc
                ),
                end_time=datetime.combine(work_date, datetime.min.time()).replace(
                    hour=17, tzinfo=timezone.utc
                ),
                summary=f"Day {i+1} work",
            )

        await session.commit()

        # Generate timecard
        timecard = await work_session_service.generate_timecard(
            start_date=start_date,
            end_date=date(2024, 1, 17),
        )

        assert len(timecard) == 3
        # Each day should have 8 hours
        for entry in timecard:
            assert entry["total_hours"] == Decimal("8.0")

    async def test_timecard_multiple_sessions_same_day_aggregated(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard aggregates multiple sessions on same day."""
        work_date = date(2024, 1, 15)

        # Create 3 sessions on same day
        sessions_data = [
            (
                datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            ),  # 1.5h
            (
                datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 13, 15, tzinfo=timezone.utc),
            ),  # 2.5h
            (
                datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 15, 17, 45, tzinfo=timezone.utc),
            ),  # 4.0h
        ]

        for start, end in sessions_data:
            await work_session_service.create_work_session(
                project_id=project_alpha.id,
                start_time=start,
                end_time=end,
            )

        await session.commit()

        # Generate timecard
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
        )

        # Should have 1 entry with total of 1.5 + 2.5 + 4.0 = 8.0 hours
        assert len(timecard) == 1
        assert timecard[0]["total_hours"] == Decimal("8.0")
        assert timecard[0]["date"] == work_date
        assert timecard[0]["project_id"] == project_alpha.id

    async def test_timecard_multiple_projects_same_day(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
        project_beta: Project,
    ):
        """Test timecard with multiple projects on same day."""
        work_date = date(2024, 1, 15)

        # Create sessions for both projects on same day
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            summary="Alpha work",
        )
        await work_session_service.create_work_session(
            project_id=project_beta.id,
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
            summary="Beta work",
        )

        await session.commit()

        # Generate timecard
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
        )

        # Should have 2 entries (one per project)
        assert len(timecard) == 2
        project_ids = {entry["project_id"] for entry in timecard}
        assert project_alpha.id in project_ids
        assert project_beta.id in project_ids

    async def test_timecard_privacy_filter_exclude_private(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard respects privacy filter."""
        work_date = date(2024, 1, 15)

        # Create sessions with different privacy levels
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PUBLIC,
        )
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PRIVATE,
        )

        await session.commit()

        # Generate timecard excluding private sessions
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
            include_private=False,
        )

        # Should only include PUBLIC session (2.0 hours)
        assert len(timecard) == 1
        assert timecard[0]["total_hours"] == Decimal("2.0")

    async def test_timecard_privacy_filter_include_private(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard includes private when requested."""
        work_date = date(2024, 1, 15)

        # Create sessions with different privacy levels
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PUBLIC,
        )
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            privacy_level=PrivacyLevel.PRIVATE,
        )

        await session.commit()

        # Generate timecard including private sessions
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
            include_private=True,
        )

        # Should include both sessions (4.0 hours total)
        assert len(timecard) == 1
        assert timecard[0]["total_hours"] == Decimal("4.0")

    async def test_timecard_summary_aggregation(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard aggregates summaries from multiple sessions."""
        work_date = date(2024, 1, 15)

        # Create sessions with different summaries
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            summary="Morning: Feature development",
        )
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            summary="Afternoon: Bug fixes",
        )

        await session.commit()

        # Generate timecard
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
        )

        # Summary should combine both
        assert len(timecard) == 1
        summary = timecard[0]["summary"]
        assert "Morning: Feature development" in summary
        assert "Afternoon: Bug fixes" in summary

    async def test_timecard_date_range_filtering(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
    ):
        """Test timecard respects date range."""
        # Create sessions across multiple weeks
        dates = [date(2024, 1, 10), date(2024, 1, 15), date(2024, 1, 20)]
        for d in dates:
            await work_session_service.create_work_session(
                project_id=project_alpha.id,
                start_time=datetime.combine(d, datetime.min.time()).replace(
                    hour=9, tzinfo=timezone.utc
                ),
                end_time=datetime.combine(d, datetime.min.time()).replace(
                    hour=17, tzinfo=timezone.utc
                ),
            )

        await session.commit()

        # Generate timecard for Jan 12-18 (should only include Jan 15)
        timecard = await work_session_service.generate_timecard(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 18),
        )

        assert len(timecard) == 1
        assert timecard[0]["date"] == date(2024, 1, 15)

    async def test_timecard_project_filter(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
        project_alpha: Project,
        project_beta: Project,
    ):
        """Test timecard can filter by project."""
        work_date = date(2024, 1, 15)

        # Create sessions for both projects
        await work_session_service.create_work_session(
            project_id=project_alpha.id,
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        )
        await work_session_service.create_work_session(
            project_id=project_beta.id,
            start_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        )

        await session.commit()

        # Generate timecard for Project Alpha only
        timecard = await work_session_service.generate_timecard(
            start_date=work_date,
            end_date=work_date,
            project_id=project_alpha.id,
        )

        # Should only include Project Alpha
        assert len(timecard) == 1
        assert timecard[0]["project_id"] == project_alpha.id

    async def test_timecard_empty_range(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
    ):
        """Test timecard returns empty list when no sessions in range."""
        timecard = await work_session_service.generate_timecard(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert timecard == []

    async def test_timecard_invalid_date_range(
        self,
        work_session_service: WorkSessionService,
        session: AsyncSession,
    ):
        """Test timecard raises error for invalid date range."""
        with pytest.raises(ValueError, match="end_date must be after or equal to start_date"):
            await work_session_service.generate_timecard(
                start_date=date(2024, 1, 31),
                end_date=date(2024, 1, 1),
            )
