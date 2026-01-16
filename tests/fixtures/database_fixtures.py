"""Database fixtures for testing with PostgreSQL test database."""

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.mosaic.models.base import Base

# Test database URL - use separate test database on PostgreSQL
TEST_DATABASE_URL = (
    "postgresql+asyncpg://mosaic:changeme_supersecret_password@localhost:5433/mosaic_test"
)


@pytest.fixture(scope="function")
async def test_engine() -> AsyncEngine:
    """
    Create PostgreSQL test database engine for each test.

    Uses function scope so each test gets a fresh database state.
    Uses PostgreSQL because models use ARRAY and JSONB types.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables (cleanup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker:
    """
    Create session factory for test database.

    This mimics the production async_session_factory but uses test database.
    """
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture(scope="function")
async def test_session(test_session_factory: async_sessionmaker) -> AsyncSession:
    """
    Create test database session.

    Each test gets a fresh session that is rolled back after the test.
    This ensures test isolation.
    """
    async with test_session_factory() as session:
        yield session
        # Always rollback to ensure no data persists
        await session.rollback()
