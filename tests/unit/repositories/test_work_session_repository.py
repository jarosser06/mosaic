"""Unit tests for WorkSessionRepository timecard queries."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.repositories.work_session_repository import WorkSessionRepository


class TestWorkSessionRepositoryBasicQueries:
    """Test basic work session queries."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> WorkSessionRepository:
        """Create work session repository."""
        return WorkSessionRepository(session)

    async def test_get_by_id_with_project(
        self, repo: WorkSessionRepository, session: AsyncSession, project: Project
    ):
        """Test getting work session with project eagerly loaded."""
        # Create work session
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("1.0"),
        )
        session.add(ws)
        await session.flush()
        await session.refresh(ws)

        # Retrieve with project
        result = await repo.get_by_id_with_project(ws.id)

        assert result is not None
        assert result.id == ws.id
        assert result.project is not None
        assert result.project.name == "Test Project"

    async def test_list_by_project(
        self, repo: WorkSessionRepository, session: AsyncSession, project: Project
    ):
        """Test listing work sessions for a project."""
        # Create multiple work sessions for same project
        for i in range(3):
            ws = WorkSession(
                project_id=project.id,
                date=date(2024, 1, 15 + i),
                start_time=datetime(2024, 1, 15 + i, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15 + i, 10, 0, tzinfo=timezone.utc),
                duration_hours=Decimal("1.0"),
            )
            session.add(ws)
        await session.flush()

        # List by project
        result = await repo.list_by_project(project.id)

        assert len(result) == 3
        for ws in result:
            assert ws.project_id == project.id

    async def test_list_by_date_range(
        self, repo: WorkSessionRepository, session: AsyncSession, project: Project
    ):
        """Test listing work sessions in date range."""
        # Create work sessions across multiple days
        dates = [date(2024, 1, 10), date(2024, 1, 15), date(2024, 1, 20)]
        for d in dates:
            ws = WorkSession(
                project_id=project.id,
                date=d,
                start_time=datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc),
                end_time=datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc),
                duration_hours=Decimal("1.0"),
            )
            session.add(ws)
        await session.flush()

        # Query date range (Jan 12-18 should get only Jan 15)
        result = await repo.list_by_date_range(
            date(2024, 1, 12),
            date(2024, 1, 18),
        )

        assert len(result) == 1
        assert result[0].date == date(2024, 1, 15)

    async def test_list_by_date_range_end_before_start_raises_error(
        self, repo: WorkSessionRepository
    ):
        """Test date range with end before start raises ValueError."""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            await repo.list_by_date_range(
                date(2024, 1, 20),
                date(2024, 1, 10),
            )


class TestWorkSessionRepositoryTimecardAggregation:
    """Test timecard data aggregation - CRITICAL for timecard generation."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> WorkSessionRepository:
        """Create work session repository."""
        return WorkSessionRepository(session)

    @pytest.fixture
    async def project_with_sessions(
        self,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ) -> Project:
        """Create project with multiple work sessions."""
        # Create project
        project = Project(
            name="Timecard Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
        )
        session.add(project)
        await session.flush()
        await session.refresh(project)

        # Create work sessions
        sessions_data = [
            # Jan 15: 2 sessions totaling 3.5 hours
            (date(2024, 1, 15), Decimal("2.0"), PrivacyLevel.PUBLIC),
            (date(2024, 1, 15), Decimal("1.5"), PrivacyLevel.PUBLIC),
            # Jan 16: 1 session, 4.0 hours
            (date(2024, 1, 16), Decimal("4.0"), PrivacyLevel.INTERNAL),
            # Jan 17: 1 session, 2.5 hours (PRIVATE)
            (date(2024, 1, 17), Decimal("2.5"), PrivacyLevel.PRIVATE),
        ]

        for work_date, hours, privacy in sessions_data:
            ws = WorkSession(
                project_id=project.id,
                date=work_date,
                start_time=datetime.combine(work_date, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                ),
                end_time=datetime.combine(work_date, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                ),
                duration_hours=hours,
                privacy_level=privacy,
            )
            session.add(ws)

        await session.flush()
        return project

    async def test_get_timecard_data_no_filter(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project_with_sessions: Project,
    ):
        """Test timecard aggregation without privacy filter."""
        entries = await repo.get_timecard_data(
            date(2024, 1, 15),
            date(2024, 1, 17),
        )

        assert len(entries) == 3
        # Check Jan 15 entry (2 sessions aggregated)
        jan_15 = [e for e in entries if e.date == date(2024, 1, 15)][0]
        assert jan_15.total_hours == Decimal("3.5")
        assert jan_15.project_name == "Timecard Project"

    async def test_get_timecard_data_public_only(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project_with_sessions: Project,
    ):
        """Test timecard with PUBLIC filter (most restrictive)."""
        entries = await repo.get_timecard_data(
            date(2024, 1, 15),
            date(2024, 1, 17),
            privacy_filter=PrivacyLevel.PUBLIC,
        )

        # Should only include Jan 15 (PUBLIC sessions)
        assert len(entries) == 1
        assert entries[0].date == date(2024, 1, 15)
        assert entries[0].total_hours == Decimal("3.5")

    async def test_get_timecard_data_internal_filter(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project_with_sessions: Project,
    ):
        """Test timecard with INTERNAL filter (includes PUBLIC + INTERNAL)."""
        entries = await repo.get_timecard_data(
            date(2024, 1, 15),
            date(2024, 1, 17),
            privacy_filter=PrivacyLevel.INTERNAL,
        )

        # Should include Jan 15 (PUBLIC) and Jan 16 (INTERNAL), but not Jan 17 (PRIVATE)
        assert len(entries) == 2
        dates = [e.date for e in entries]
        assert date(2024, 1, 15) in dates
        assert date(2024, 1, 16) in dates
        assert date(2024, 1, 17) not in dates

    async def test_get_timecard_data_private_filter(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project_with_sessions: Project,
    ):
        """Test timecard with PRIVATE filter (includes all)."""
        entries = await repo.get_timecard_data(
            date(2024, 1, 15),
            date(2024, 1, 17),
            privacy_filter=PrivacyLevel.PRIVATE,
        )

        # Should include all sessions
        assert len(entries) == 3

    async def test_get_timecard_data_date_range_validation(self, repo: WorkSessionRepository):
        """Test timecard with invalid date range raises error."""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            await repo.get_timecard_data(
                date(2024, 1, 20),
                date(2024, 1, 10),
            )

    async def test_get_total_hours_by_project(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project_with_sessions: Project,
    ):
        """Test getting total hours for a project in date range."""
        total = await repo.get_total_hours_by_project(
            project_with_sessions.id,
            date(2024, 1, 15),
            date(2024, 1, 17),
        )

        # Total: 3.5 + 4.0 + 2.5 = 10.0
        assert total == Decimal("10.0")

    async def test_get_total_hours_no_sessions_returns_zero(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test total hours returns 0.0 when no sessions exist."""
        total = await repo.get_total_hours_by_project(
            project.id,
            date(2024, 1, 1),
            date(2024, 1, 31),
        )

        assert total == Decimal("0.0")

    async def test_timecard_multiple_projects(
        self,
        repo: WorkSessionRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test timecard aggregation with multiple projects."""
        # Create two projects
        project1 = Project(name="Project 1", on_behalf_of_id=employer.id, client_id=client.id)
        project2 = Project(name="Project 2", on_behalf_of_id=employer.id, client_id=client.id)
        session.add(project1)
        session.add(project2)
        await session.flush()

        # Add sessions for both projects on same date
        ws1 = WorkSession(
            project_id=project1.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("2.0"),
        )
        ws2 = WorkSession(
            project_id=project2.id,
            date=date(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
        )
        session.add(ws1)
        session.add(ws2)
        await session.flush()

        # Get timecard data
        entries = await repo.get_timecard_data(
            date(2024, 1, 15),
            date(2024, 1, 15),
        )

        # Should have 2 entries (one per project)
        assert len(entries) == 2
        project_names = {e.project_name for e in entries}
        assert "Project 1" in project_names
        assert "Project 2" in project_names
