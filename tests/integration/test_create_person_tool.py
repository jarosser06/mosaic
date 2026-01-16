"""Integration tests for add_person MCP tool.

Tests end-to-end person creation through real MCP server,
including validation, optional fields, and database persistence.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.schemas.person import AddPersonInput
from src.mosaic.tools.logging_tools import add_person


class TestAddPersonTool:
    """Test add_person tool with real MCP server."""

    @pytest.mark.asyncio
    async def test_add_person_minimal(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with only required fields through real MCP tool."""
        input_data = AddPersonInput(
            full_name="John Doe",
        )

        # Call REAL tool with REAL MCP context
        result = await add_person(input_data, mcp_client)

        # Verify result
        assert result.id is not None
        assert result.full_name == "John Doe"
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title is None

        # Verify database persistence
        from src.mosaic.repositories.person_repository import PersonRepository

        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(result.id)
        assert fetched is not None
        assert fetched.full_name == "John Doe"

    @pytest.mark.asyncio
    async def test_add_person_with_email(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with email."""
        input_data = AddPersonInput(
            full_name="Jane Smith",
            email="jane@example.com",
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.full_name == "Jane Smith"
        assert result.email == "jane@example.com"

    @pytest.mark.asyncio
    async def test_add_person_with_phone(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with phone."""
        input_data = AddPersonInput(
            full_name="Bob Johnson",
            phone="+1-555-123-4567",
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.phone == "+1-555-123-4567"

    @pytest.mark.asyncio
    async def test_add_person_with_company_and_title(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with company and title."""
        input_data = AddPersonInput(
            full_name="Alice Williams",
            company="Acme Corp",
            title="Senior Engineer",
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.company == "Acme Corp"
        assert result.title == "Senior Engineer"

    @pytest.mark.asyncio
    async def test_add_person_with_notes(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with notes."""
        input_data = AddPersonInput(
            full_name="Charlie Brown",
            notes="Met at conference 2025. Interested in collaboration.",
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.notes == "Met at conference 2025. Interested in collaboration."

    @pytest.mark.asyncio
    async def test_add_person_with_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with tags."""
        input_data = AddPersonInput(
            full_name="Diana Prince",
            tags=["client", "technical", "decision-maker"],
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.tags == ["client", "technical", "decision-maker"]

    @pytest.mark.asyncio
    async def test_add_person_all_fields(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test adding person with all fields populated."""
        input_data = AddPersonInput(
            full_name="Eve Adams",
            email="eve@tech.com",
            phone="+1-555-999-8888",
            company="Tech Solutions Inc",
            title="CTO",
            notes="Key technical contact for project Alpha",
            tags=["client", "executive", "technical"],
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.full_name == "Eve Adams"
        assert result.email == "eve@tech.com"
        assert result.phone == "+1-555-999-8888"
        assert result.company == "Tech Solutions Inc"
        assert result.title == "CTO"
        assert result.notes == "Key technical contact for project Alpha"
        assert result.tags == ["client", "executive", "technical"]

    @pytest.mark.asyncio
    async def test_add_person_persisted_to_database(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test that person is persisted to database."""
        from src.mosaic.repositories.person_repository import PersonRepository

        input_data = AddPersonInput(
            full_name="Frank Miller",
            email="frank@example.com",
        )

        result = await add_person(input_data, mcp_client)

        # Verify it's in the database
        repo = PersonRepository(test_session)
        fetched = await repo.get_by_id(result.id)

        assert fetched is not None
        assert fetched.full_name == "Frank Miller"
        assert fetched.email == "frank@example.com"
