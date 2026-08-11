"""
Async SQLAlchemy database engine, session factory, and base dependency.
"""
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Engine Construction (PostgreSQL vs SQLite support)
# ──────────────────────────────────────────────────────────────────────────────
is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    engine_kwargs: dict[str, Any] = {
        "echo": settings.db_echo,
    }
else:
    engine_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_pre_ping": True,
        "echo": settings.db_echo,
    }

engine = create_async_engine(settings.database_url, **engine_kwargs)

# ──────────────────────────────────────────────────────────────────────────────
# Session Factory
# ──────────────────────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ──────────────────────────────────────────────────────────────────────────────
# Base Model
# ──────────────────────────────────────────────────────────────────────────────
class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    AsyncAttrs enables awaitable lazy loading on relationships.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary (non-relationship columns only)."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }


# ──────────────────────────────────────────────────────────────────────────────
# Dependency
# ──────────────────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
