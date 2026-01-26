"""Unit tests for WorkSessionService (simplified: date + duration only)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.services.work_session_service import WorkSessionService


class TestWorkSessionServiceCreate:
    """Test work session creation through service layer."""

    @pytest.fixture
    async def service(self, session: AsyncSession) -> WorkSessionService:
        """Create work session service."""
        return WorkSessionService(session)

    @pytest.mark.asyncio
    async def test_create_work_session_valid(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating work session with valid inputs."""
        work_date = date(2024, 1, 15)
        duration = Decimal("8.0")

        work_session = await service.create_work_session(
            project_id=project.id,
            date=work_date,
            duration_hours=duration,
            summary="Implemented feature X",
        )

        assert work_session.id is not None
        assert work_session.project_id == project.id
        assert work_session.date == work_date
        assert work_session.duration_hours == duration
        assert work_session.summary == "Implemented feature X"
        assert work_session.privacy_level == PrivacyLevel.PRIVATE

    @pytest.mark.asyncio
    async def test_create_work_session_with_all_fields(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating work session with all optional fields."""
        work_session = await service.create_work_session(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("4.5"),
            summary="Backend development",
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["backend", "api"],
        )

        assert work_session.summary == "Backend development"
        assert work_session.privacy_level == PrivacyLevel.INTERNAL
        assert work_session.tags == ["backend", "api"]
        assert work_session.duration_hours == Decimal("4.5")

    @pytest.mark.asyncio
    async def test_create_work_session_invalid_project_id(
        self,
        service: WorkSessionService,
        session: AsyncSession,
    ):
        """Test creating work session with non-existent project raises error."""
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await service.create_work_session(
                project_id=99999,  # Non-existent
                date=date(2024, 1, 15),
                duration_hours=Decimal("8.0"),
            )

    @pytest.mark.asyncio
    async def test_create_work_session_zero_duration(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating work session with zero duration raises error."""
        with pytest.raises(ValueError, match="Duration must be greater than 0"):
            await service.create_work_session(
                project_id=project.id,
                date=date(2024, 1, 15),
                duration_hours=Decimal("0.0"),
            )

    @pytest.mark.asyncio
    async def test_create_work_session_negative_duration(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating work session with negative duration raises error."""
        with pytest.raises(ValueError, match="Duration must be greater than 0"):
            await service.create_work_session(
                project_id=project.id,
                date=date(2024, 1, 15),
                duration_hours=Decimal("-1.0"),
            )

    @pytest.mark.asyncio
    async def test_create_work_session_duration_over_24(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating work session with duration > 24 raises error."""
        with pytest.raises(ValueError, match="Duration must not exceed 24 hours"):
            await service.create_work_session(
                project_id=project.id,
                date=date(2024, 1, 15),
                duration_hours=Decimal("24.1"),
            )


class TestWorkSessionServiceUpdate:
    """Test work session update operations."""

    @pytest.fixture
    async def service(self, session: AsyncSession) -> WorkSessionService:
        """Create work session service."""
        return WorkSessionService(session)

    @pytest.fixture
    async def existing_work_session(self, session: AsyncSession, project: Project) -> WorkSession:
        """Create an existing work session for update tests."""
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15),
            duration_hours=Decimal("8.0"),
            summary="Original summary",
        )
        session.add(ws)
        await session.flush()
        await session.refresh(ws)
        return ws

    @pytest.mark.asyncio
    async def test_update_work_session_date(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        existing_work_session: WorkSession,
    ):
        """Test updating work session date."""
        new_date = date(2024, 1, 16)

        updated = await service.update_work_session(
            work_session_id=existing_work_session.id,
            date=new_date,
        )

        assert updated.date == new_date
        assert updated.duration_hours == Decimal("8.0")  # Unchanged

    @pytest.mark.asyncio
    async def test_update_work_session_duration(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        existing_work_session: WorkSession,
    ):
        """Test updating work session duration."""
        new_duration = Decimal("4.5")

        updated = await service.update_work_session(
            work_session_id=existing_work_session.id,
            duration_hours=new_duration,
        )

        assert updated.duration_hours == new_duration
        assert updated.date == date(2024, 1, 15)  # Unchanged

    @pytest.mark.asyncio
    async def test_update_work_session_project_id(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        existing_work_session: WorkSession,
        employer,
        client,
    ):
        """Test updating work session project_id."""
        # Create another project
        from src.mosaic.models.project import Project

        new_project = Project(
            name="New Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
        )
        session.add(new_project)
        await session.flush()

        updated = await service.update_work_session(
            work_session_id=existing_work_session.id,
            project_id=new_project.id,
        )

        assert updated.project_id == new_project.id

    @pytest.mark.asyncio
    async def test_update_work_session_multiple_fields(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        existing_work_session: WorkSession,
    ):
        """Test updating multiple fields at once."""
        updated = await service.update_work_session(
            work_session_id=existing_work_session.id,
            date=date(2024, 1, 20),
            duration_hours=Decimal("6.0"),
            summary="Updated summary",
            privacy_level=PrivacyLevel.PUBLIC,
        )

        assert updated.date == date(2024, 1, 20)
        assert updated.duration_hours == Decimal("6.0")
        assert updated.summary == "Updated summary"
        assert updated.privacy_level == PrivacyLevel.PUBLIC

    @pytest.mark.asyncio
    async def test_update_work_session_invalid_duration(
        self,
        service: WorkSessionService,
        session: AsyncSession,
        existing_work_session: WorkSession,
    ):
        """Test updating work session with invalid duration raises error."""
        with pytest.raises(ValueError, match="Duration must not exceed 24 hours"):
            await service.update_work_session(
                work_session_id=existing_work_session.id,
                duration_hours=Decimal("25.0"),
            )

    @pytest.mark.asyncio
    async def test_update_work_session_nonexistent(
        self,
        service: WorkSessionService,
        session: AsyncSession,
    ):
        """Test updating non-existent work session raises error."""
        with pytest.raises(ValueError, match="WorkSession with id 99999 not found"):
            await service.update_work_session(
                work_session_id=99999,
                duration_hours=Decimal("4.0"),
            )
