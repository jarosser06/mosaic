"""Unit tests for ProjectRepository custom queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project, ProjectStatus
from src.mosaic.repositories.project_repository import ProjectRepository


class TestProjectRepositoryQueries:
    """Test ProjectRepository custom query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> ProjectRepository:
        """Create project repository."""
        return ProjectRepository(session)

    async def test_get_by_name_existing(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test finding project by name."""
        # Create projects
        project1 = Project(
            name="Project Alpha",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project2 = Project(
            name="Project Beta",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        session.add_all([project1, project2])
        await session.flush()

        # Find by name
        result = await repo.get_by_name("Project Beta")

        assert result is not None
        assert result.name == "Project Beta"

    async def test_get_by_name_nonexistent(self, repo: ProjectRepository):
        """Test finding project by name returns None when not found."""
        result = await repo.get_by_name("Nonexistent Project")
        assert result is None

    async def test_list_active_projects_only(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test listing only active projects."""
        # Create projects with different statuses
        active1 = Project(
            name="Active Project 1",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        active2 = Project(
            name="Active Project 2",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        paused = Project(
            name="Paused Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.PAUSED,
        )
        completed = Project(
            name="Completed Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.COMPLETED,
        )
        session.add_all([active1, active2, paused, completed])
        await session.flush()

        # List active only
        result = await repo.list_active()

        assert len(result) == 2
        names = {p.name for p in result}
        assert "Active Project 1" in names
        assert "Active Project 2" in names
        assert "Paused Project" not in names
        assert "Completed Project" not in names

    async def test_list_by_employer(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        client: Client,
    ):
        """Test listing projects by employer."""
        # Create two employers
        employer1 = Employer(name="Employer 1")
        employer2 = Employer(name="Employer 2")
        session.add_all([employer1, employer2])
        await session.flush()

        # Create projects for different employers
        project1 = Project(
            name="Employer 1 Project A",
            on_behalf_of_id=employer1.id,
            client_id=client.id,
        )
        project2 = Project(
            name="Employer 1 Project B",
            on_behalf_of_id=employer1.id,
            client_id=client.id,
        )
        project3 = Project(
            name="Employer 2 Project",
            on_behalf_of_id=employer2.id,
            client_id=client.id,
        )
        session.add_all([project1, project2, project3])
        await session.flush()

        # List by employer 1
        results = await repo.list_by_employer(employer1.id)

        assert len(results) == 2
        names = {p.name for p in results}
        assert "Employer 1 Project A" in names
        assert "Employer 1 Project B" in names
        assert "Employer 2 Project" not in names

    async def test_list_by_client(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
    ):
        """Test listing projects by client."""
        # Create two clients
        client1 = Client(name="Client 1", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
        client2 = Client(name="Client 2", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
        session.add_all([client1, client2])
        await session.flush()

        # Create projects for different clients
        project1 = Project(
            name="Client 1 Project A",
            on_behalf_of_id=employer.id,
            client_id=client1.id,
        )
        project2 = Project(
            name="Client 1 Project B",
            on_behalf_of_id=employer.id,
            client_id=client1.id,
        )
        project3 = Project(
            name="Client 2 Project",
            on_behalf_of_id=employer.id,
            client_id=client2.id,
        )
        session.add_all([project1, project2, project3])
        await session.flush()

        # List by client 1
        results = await repo.list_by_client(client1.id)

        assert len(results) == 2
        names = {p.name for p in results}
        assert "Client 1 Project A" in names
        assert "Client 1 Project B" in names
        assert "Client 2 Project" not in names

    async def test_get_by_id_with_relations(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test eager loading employer and client relations."""
        # Create project
        project = Project(
            name="Test Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            description="Test description",
        )
        session.add(project)
        await session.flush()

        # Get with relations
        result = await repo.get_by_id_with_relations(project.id)

        assert result is not None
        assert result.id == project.id
        assert result.employer is not None
        assert result.employer.name == employer.name
        assert result.client is not None
        assert result.client.name == client.name

    async def test_update_project_status(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test updating project status."""
        # Create active project
        project = await repo.create(
            name="Test Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        project_id = project.id

        # Update to paused
        updated = await repo.update(project_id, status=ProjectStatus.PAUSED)

        assert updated is not None
        assert updated.status == ProjectStatus.PAUSED

        # Verify not in active list
        active_projects = await repo.list_active()
        assert len(active_projects) == 0

    async def test_create_project_with_description(
        self,
        repo: ProjectRepository,
        session: AsyncSession,
        employer: Employer,
        client: Client,
    ):
        """Test creating project with full details."""
        project = await repo.create(
            name="Detailed Project",
            on_behalf_of_id=employer.id,
            client_id=client.id,
            description="This is a detailed project description",
            status=ProjectStatus.ACTIVE,
        )

        assert project.id is not None
        assert project.name == "Detailed Project"
        assert project.description == "This is a detailed project description"
        assert project.status == ProjectStatus.ACTIVE

    async def test_list_by_employer_empty(self, repo: ProjectRepository, employer: Employer):
        """Test listing projects for employer with no projects."""
        results = await repo.list_by_employer(employer.id)
        assert results == []

    async def test_list_by_client_empty(self, repo: ProjectRepository, client: Client):
        """Test listing projects for client with no projects."""
        results = await repo.list_by_client(client.id)
        assert results == []

    async def test_list_active_empty(self, repo: ProjectRepository):
        """Test listing active projects when none exist."""
        result = await repo.list_active()
        assert result == []
