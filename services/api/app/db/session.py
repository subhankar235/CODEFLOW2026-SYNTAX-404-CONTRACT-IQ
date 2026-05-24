"""Database session configuration and engine setup."""

import sys as _sys
from pathlib import Path as _Path

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ..core.config import settings


def _get_database_url() -> str:
    """Get the async database URL from settings."""
    # Convert Neon psycopg:// URL to asyncpg:// for async support
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("psycopg://"):
        url = url.replace("psycopg://", "postgresql+asyncpg://", 1)

    # Remove SSL-related parameters that asyncpg doesn't support
    # asyncpg uses SSL by default for secure connections
    if "?" in url:
        base_url = url.split("?")[0]
        params = url.split("?", 1)[1]
        # Keep only parameters that asyncpg supports
        # Remove sslmode, channel_binding, etc.
        keep_params = []
        for param in params.split("&"):
            if not any(skip in param for skip in ["sslmode", "channel_binding", "ssl"]):
                keep_params.append(param)
        if keep_params:
            url = base_url + "?" + "&".join(keep_params)
        else:
            url = base_url

    return url


# Determine if using serverless (Neon)
_use_null_pool = "neon" in settings.database_url

# Create async engine with appropriate pool settings
if _use_null_pool:
    engine = create_async_engine(
        _get_database_url(),
        echo=settings.environment == "development",  # Log SQL in dev mode
        future=True,
        pool_pre_ping=True,  # Test connections before using them
        poolclass=NullPool,  # No connection pooling for serverless
    )
else:
    engine = create_async_engine(
        _get_database_url(),
        echo=settings.environment == "development",  # Log SQL in dev mode
        future=True,
        pool_pre_ping=True,  # Test connections before using them
        pool_size=20,  # Connection pool size
        max_overflow=10,  # Additional overflow connections
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

SessionLocal = AsyncSessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
