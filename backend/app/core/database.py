"""
SIH 26090: Database Engine & Session Management
Provides async SQLAlchemy 2.0 engine, session factory, and dependency injection helpers.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.core.config import settings
from backend.app.core.telemetry import logger

# Base class for declarative SQLAlchemy models
Base = declarative_base()

# Configure Async Engine for FastAPI requests
engine_kwargs = {}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE_SECONDS,
    })

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    future=True,
    **engine_kwargs
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Sync engine helper for scripts and migrations
# In SQLAlchemy 2.0 with psycopg v3 installed, use postgresql+psycopg:// for sync connections
sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg").replace("+aiosqlite", "")
sync_engine = create_engine(
    sync_db_url,
    echo=False,
    future=True
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session scoped per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rolled back due to error: {e}", exc_info=True)
            raise
        finally:
            await session.close()
