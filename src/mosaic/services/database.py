"""Async database session management."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config

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


def _run_migrations() -> None:
    """Run Alembic migrations synchronously."""
    # Find the project root (where alembic.ini lives)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent  # src/mosaic/services -> project root

    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning(f"alembic.ini not found at {alembic_ini}, skipping auto-migration")
        return

    alembic_cfg = Config(str(alembic_ini))
    # Set the script location relative to project root
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

    logger.info("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations complete")


async def init_db() -> None:
    """Initialize database: create if needed and run migrations."""
    # First ensure database exists
    await _ensure_database_exists()

    # Run Alembic migrations in a thread pool (Alembic is synchronous)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_migrations)


async def close_db() -> None:
    """Close database engine (for application shutdown)."""
    await engine.dispose()
