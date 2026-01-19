"""Async database session management."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .. import models  # noqa: F401 - imported for side effects (model registration)
from ..models.base import Base

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Configure async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=os.getenv("LOG_LEVEL") == "DEBUG",
    pool_pre_ping=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            # perform database operations
            pass

    Note:
        Does not auto-begin transactions. For read-only queries,
        no transaction is needed. For writes, wrap in session.begin().
    """
    session = async_session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class DatabaseConfig:
    """Parsed database connection configuration."""

    def __init__(
        self,
        user: str | None,
        password: str | None,
        host: str,
        port: int,
        database: str | None,
    ) -> None:
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database


def _parse_database_url(url: str) -> DatabaseConfig:
    """Parse DATABASE_URL into components."""
    # Handle both postgresql+asyncpg:// and postgresql:// schemes
    parsed = urlparse(url.replace("+asyncpg", ""))
    return DatabaseConfig(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") if parsed.path else None,
    )


async def _ensure_database_exists() -> None:
    """Create the database if it doesn't exist."""
    if not DATABASE_URL:
        return

    db_config = _parse_database_url(DATABASE_URL)
    db_name = db_config.database

    if not db_name:
        logger.warning("No database name in DATABASE_URL, skipping database creation")
        return

    # Connect to default 'postgres' database to check/create target database
    try:
        conn = await asyncpg.connect(
            user=db_config.user,
            password=db_config.password,
            host=db_config.host,
            port=db_config.port,
            database="postgres",  # Connect to default database
        )

        try:
            # Check if database exists
            exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)

            if not exists:
                logger.info(f"Database '{db_name}' does not exist, creating...")
                # CREATE DATABASE cannot run inside a transaction
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.debug(f"Database '{db_name}' already exists")
        finally:
            await conn.close()

    except asyncpg.InvalidCatalogNameError:
        # Database doesn't exist - this shouldn't happen since we connect to 'postgres'
        logger.error("Could not connect to 'postgres' database")
        raise
    except Exception as e:
        logger.error(f"Error ensuring database exists: {e}")
        raise


async def _create_tables() -> None:
    """Create all database tables using SQLAlchemy metadata.

    This uses Base.metadata.create_all() which is idempotent:
    - Checks which tables already exist
    - Only creates missing tables
    - Safe to run on every startup

    Raises:
        Exception: If table creation fails
    """
    try:
        logger.info("Creating database tables...")

        # Use engine.begin() to get async connection with transaction
        async with engine.begin() as conn:
            # Run synchronous create_all in the async connection
            # This imports all models via Base.metadata and creates tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def init_db() -> None:
    """Initialize database: create database if needed and create tables.

    This is called on server startup to ensure the database and all
    tables exist before processing any requests.
    """
    # First ensure database exists
    await _ensure_database_exists()

    # Create all tables (idempotent - safe to run multiple times)
    await _create_tables()


async def close_db() -> None:
    """Close database engine (for application shutdown)."""
    await engine.dispose()
