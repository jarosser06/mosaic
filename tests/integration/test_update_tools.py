"""Integration tests for update MCP tools using real MCP server.

Tests end-to-end update operations for work sessions, meetings, people,
clients, projects, notes, and reminders through MCP tool interface.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.repositories.person_repository import PersonRepository
from src.mosaic.repositories.work_session_repository import WorkSessionRepository
from src.mosaic.schemas.person import UpdatePersonInput
from src.mosaic.schemas.work_session import UpdateWorkSessionInput
from src.mosaic.tools.update_tools import update_person, update_work_session


class TestUpdateTools:
    """Test update MCP tools end-to-end with real MCP server."""

    @pytest.mark.asyncio
    async def test_update_work_session_description(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test updating work session description through real MCP tool."""
        # Create a work session with summary (model field name)
        start_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        ws = WorkSession(
            project_id=project.id,
            date=start_time.date(),
            start_time=start_time,
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Original description",
        )
        test_session.add(ws)
        await test_session.commit()  # Commit so tool can see it
        await test_session.refresh(ws)

        # Update description (schema field name) via REAL MCP tool
        input_data = UpdateWorkSessionInput(
            description="Updated description",
        )

        ws_id = ws.id  # Store ID before closing session
        result = await update_work_session(ws_id, input_data, mcp_client)

        # Verify result
        assert result.id == ws_id
        assert result.description == "Updated description"

        # Verify database persistence with fresh session
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = WorkSessionRepository(fresh_session)
            fetched = await repo.get_by_id(ws_id)
            assert fetched is not None
            assert fetched.summary == "Updated description"

    @pytest.mark.asyncio
    async def test_update_work_session_times(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test updating work session times recalculates duration."""
        # Create a work session (3 hours)
        start_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        ws = WorkSession(
            project_id=project.id,
            date=start_time.date(),
            start_time=start_time,
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        # Update to 4 hours via REAL MCP tool
        input_data = UpdateWorkSessionInput(
            end_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc),
        )

        result = await update_work_session(ws.id, input_data, mcp_client)

        # Verify duration recalculated
        assert result.duration_hours == 4.0

        # Verify database persistence
        await test_session.commit()
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(ws.id)
        assert fetched is not None
        assert fetched.duration_hours == Decimal("4.0")

    @pytest.mark.asyncio
    async def test_update_work_session_privacy_level(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test updating work session privacy level."""
        # Create a private work session
        start_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        ws = WorkSession(
            project_id=project.id,
            date=start_time.date(),
            start_time=start_time,
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            privacy_level=PrivacyLevel.PRIVATE,
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        # Update to public via REAL MCP tool
        input_data = UpdateWorkSessionInput(
            privacy_level=PrivacyLevel.PUBLIC,
        )

        result = await update_work_session(ws.id, input_data, mcp_client)

        # Verify result
        assert result.privacy_level == PrivacyLevel.PUBLIC

        # Verify database persistence
        await test_session.commit()
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(ws.id)
        assert fetched is not None
        assert fetched.privacy_level == PrivacyLevel.PUBLIC

    @pytest.mark.asyncio
    async def test_update_work_session_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test updating work session tags."""
        # Create work session with tags
        start_time = datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc)
        ws = WorkSession(
            project_id=project.id,
            date=start_time.date(),
            start_time=start_time,
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            tags=["old", "tag"],
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        # Update tags via REAL MCP tool
        input_data = UpdateWorkSessionInput(
            tags=["new", "updated", "tags"],
        )

        result = await update_work_session(ws.id, input_data, mcp_client)

        # Verify result
        assert result.tags == ["new", "updated", "tags"]

        # Verify database persistence
        await test_session.commit()
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(ws.id)
        assert fetched is not None
        assert fetched.tags == ["new", "updated", "tags"]

    @pytest.mark.asyncio
    async def test_update_person_name(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test updating person name through real MCP tool."""
        # Create person
        person = Person(full_name="John Doe")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        # Update name via REAL MCP tool
        input_data = UpdatePersonInput(
            full_name="John Doe Jr.",
        )

        result = await update_person(person.id, input_data, mcp_client)

        # Verify result
        assert result.id == person.id
        assert result.full_name == "John Doe Jr."

        # Verify database persistence
        await test_session.commit()
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(person.id)
        assert fetched is not None
        assert fetched.full_name == "John Doe Jr."

    @pytest.mark.asyncio
    async def test_update_person_email(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test updating person email."""
        # Create person
        person = Person(full_name="Jane Smith", email="old@example.com")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        # Update email via REAL MCP tool
        input_data = UpdatePersonInput(
            email="new@example.com",
        )

        result = await update_person(person.id, input_data, mcp_client)

        # Verify result
        assert result.email == "new@example.com"

        # Verify database persistence
        await test_session.commit()
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(person.id)
        assert fetched is not None
        assert fetched.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_person_company_and_title(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test updating person company and title."""
        # Create person
        person = Person(
            full_name="Bob Johnson",
            company="Old Corp",
            title="Engineer",
        )
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        # Update company and title via REAL MCP tool
        input_data = UpdatePersonInput(
            company="New Corp",
            title="Senior Engineer",
        )

        result = await update_person(person.id, input_data, mcp_client)

        # Verify result
        assert result.company == "New Corp"
        assert result.title == "Senior Engineer"

        # Verify database persistence
        await test_session.commit()
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(person.id)
        assert fetched is not None
        assert fetched.company == "New Corp"
        assert fetched.title == "Senior Engineer"

    @pytest.mark.asyncio
    async def test_update_person_notes(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test updating person notes."""
        # Create person
        person = Person(full_name="Alice Williams", notes="Old notes")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        # Update notes via REAL MCP tool
        input_data = UpdatePersonInput(
            notes="Updated notes with new information",
        )

        result = await update_person(person.id, input_data, mcp_client)

        # Verify result
        assert result.notes == "Updated notes with new information"

        # Verify database persistence
        await test_session.commit()
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(person.id)
        assert fetched is not None
        assert fetched.notes == "Updated notes with new information"

    @pytest.mark.asyncio
    async def test_update_person_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test updating person tags."""
        # Create person with tags
        person = Person(full_name="Charlie Brown", tags=["old", "tags"])
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        # Update tags via REAL MCP tool
        input_data = UpdatePersonInput(
            tags=["client", "active", "technical"],
        )

        result = await update_person(person.id, input_data, mcp_client)

        # Verify result
        assert result.tags == ["client", "active", "technical"]

        # Verify database persistence
        await test_session.commit()
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(person.id)
        assert fetched is not None
        assert fetched.tags == ["client", "active", "technical"]
