"""Tests for Person and EmploymentHistory models."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.base import ClientType
from src.mosaic.models.client import Client
from src.mosaic.models.person import EmploymentHistory, Person


@pytest.mark.asyncio
async def test_person_creation_minimal(session: AsyncSession) -> None:
    """Test creating person with minimal required fields."""
    person = Person(full_name="Jane Smith")
    session.add(person)
    await session.flush()
    await session.refresh(person)

    assert person.id is not None
    assert person.full_name == "Jane Smith"
    assert person.email is None
    assert person.phone is None
    assert person.linkedin_url is None
    assert person.is_stakeholder is False
    assert person.additional_info is None
    assert person.created_at is not None
    assert person.updated_at is not None


@pytest.mark.asyncio
async def test_person_creation_full(session: AsyncSession) -> None:
    """Test creating person with all fields populated."""
    person = Person(
        full_name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        linkedin_url="https://linkedin.com/in/johndoe",
        is_stakeholder=True,
        additional_info={"interests": ["Python", "AI"], "location": "NYC"},
    )
    session.add(person)
    await session.flush()
    await session.refresh(person)

    assert person.full_name == "John Doe"
    assert person.email == "john@example.com"
    assert person.phone == "+1234567890"
    assert person.linkedin_url == "https://linkedin.com/in/johndoe"
    assert person.is_stakeholder is True
    assert person.additional_info == {"interests": ["Python", "AI"], "location": "NYC"}


@pytest.mark.asyncio
async def test_person_stakeholder_flag(session: AsyncSession) -> None:
    """Test stakeholder flag functionality."""
    person = Person(full_name="Stakeholder", is_stakeholder=True)
    session.add(person)
    await session.flush()
    await session.refresh(person)

    assert person.is_stakeholder is True


@pytest.mark.asyncio
async def test_person_jsonb_additional_info(session: AsyncSession) -> None:
    """Test JSONB additional_info field."""
    complex_info = {
        "skills": ["Python", "SQL", "Docker"],
        "preferences": {"communication": "email", "timezone": "EST"},
        "notes": "Very helpful team member",
    }

    person = Person(full_name="Test Person", additional_info=complex_info)
    session.add(person)
    await session.flush()
    await session.refresh(person)

    assert person.additional_info == complex_info
    assert person.additional_info["skills"] == ["Python", "SQL", "Docker"]


@pytest.mark.asyncio
async def test_person_email_indexing(session: AsyncSession) -> None:
    """Test that person emails are indexed and queryable."""
    person1 = Person(full_name="Alice", email="alice@example.com")
    person2 = Person(full_name="Bob", email="bob@example.com")
    person3 = Person(full_name="Charlie")
    session.add_all([person1, person2, person3])
    await session.flush()

    # Query by email
    stmt = select(Person).where(Person.email == "alice@example.com")
    result = await session.execute(stmt)
    person = result.scalar_one()

    assert person.full_name == "Alice"


@pytest.mark.asyncio
async def test_employment_history_creation(session: AsyncSession) -> None:
    """Test creating employment history record."""
    person = Person(full_name="John Doe")
    client = Client(name="Acme Corp", type=ClientType.COMPANY)
    session.add_all([person, client])
    await session.flush()

    employment = EmploymentHistory(
        person_id=person.id,
        client_id=client.id,
        role="Software Engineer",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )
    session.add(employment)
    await session.flush()
    await session.refresh(employment)

    assert employment.id is not None
    assert employment.person_id == person.id
    assert employment.client_id == client.id
    assert employment.role == "Software Engineer"
    assert employment.start_date == date(2020, 1, 1)
    assert employment.end_date == date(2023, 12, 31)


@pytest.mark.asyncio
async def test_employment_history_current_employment(session: AsyncSession) -> None:
    """Test employment history with no end date (current employment)."""
    person = Person(full_name="Active Employee")
    client = Client(name="Current Employer", type=ClientType.COMPANY)
    session.add_all([person, client])
    await session.flush()

    employment = EmploymentHistory(
        person_id=person.id,
        client_id=client.id,
        role="Senior Engineer",
        start_date=date(2023, 1, 1),
        end_date=None,
    )
    session.add(employment)
    await session.flush()
    await session.refresh(employment)

    assert employment.end_date is None
    assert employment.start_date == date(2023, 1, 1)


@pytest.mark.asyncio
async def test_person_employment_relationship(session: AsyncSession) -> None:
    """Test person-employment history relationship loading."""
    person = Person(full_name="Multi-Company Person")
    client1 = Client(name="Company A", type=ClientType.COMPANY)
    client2 = Client(name="Company B", type=ClientType.COMPANY)
    session.add_all([person, client1, client2])
    await session.flush()

    emp1 = EmploymentHistory(
        person_id=person.id,
        client_id=client1.id,
        role="Developer",
        start_date=date(2018, 1, 1),
        end_date=date(2020, 12, 31),
    )
    emp2 = EmploymentHistory(
        person_id=person.id,
        client_id=client2.id,
        role="Senior Developer",
        start_date=date(2021, 1, 1),
    )
    session.add_all([emp1, emp2])
    await session.flush()

    # Reload with relationship
    stmt = select(Person).where(Person.id == person.id).options(selectinload(Person.employments))
    result = await session.execute(stmt)
    loaded_person = result.scalar_one()

    assert len(loaded_person.employments) == 2
    assert {e.role for e in loaded_person.employments} == {"Developer", "Senior Developer"}


@pytest.mark.asyncio
async def test_employment_history_cascade_delete(session: AsyncSession) -> None:
    """Test that employment history is deleted when person is deleted."""
    person = Person(full_name="Deletable Person")
    client = Client(name="Some Client", type=ClientType.COMPANY)
    session.add_all([person, client])
    await session.flush()

    employment = EmploymentHistory(
        person_id=person.id,
        client_id=client.id,
        start_date=date(2020, 1, 1),
    )
    session.add(employment)
    await session.flush()

    employment_id = employment.id

    # Delete person
    await session.delete(person)
    await session.flush()

    # Employment should be deleted
    stmt = select(EmploymentHistory).where(EmploymentHistory.id == employment_id)
    result = await session.execute(stmt)
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_employment_history_role_optional(session: AsyncSession) -> None:
    """Test employment history with no role specified."""
    person = Person(full_name="Person")
    client = Client(name="Client", type=ClientType.COMPANY)
    session.add_all([person, client])
    await session.flush()

    employment = EmploymentHistory(
        person_id=person.id,
        client_id=client.id,
        start_date=date(2020, 1, 1),
        role=None,
    )
    session.add(employment)
    await session.flush()
    await session.refresh(employment)

    assert employment.role is None


@pytest.mark.asyncio
async def test_person_full_name_indexing(session: AsyncSession) -> None:
    """Test that person names are indexed and queryable."""
    person1 = Person(full_name="Alice Anderson")
    person2 = Person(full_name="Bob Brown")
    person3 = Person(full_name="Alice Cooper")
    session.add_all([person1, person2, person3])
    await session.flush()

    # Query by name pattern
    stmt = select(Person).where(Person.full_name.like("Alice%"))
    result = await session.execute(stmt)
    people = result.scalars().all()

    assert len(people) == 2
    assert {p.full_name for p in people} == {"Alice Anderson", "Alice Cooper"}
