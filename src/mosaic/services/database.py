"""Async database session management."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
    """
    session = async_session_factory()
    try:
        async with session.begin():
            yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database engine (for application startup)."""
    # Engine is created at module level, so this is a no-op
    # But can be used for any initialization logic if needed
    pass


async def close_db() -> None:
    """Close database engine (for application shutdown)."""
    await engine.dispose()
