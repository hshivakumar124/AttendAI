"""
AttendAI — Async Database Engine & Session Factory
===================================================
Uses SQLAlchemy 2.0 async engine with asyncpg driver.
All DB operations are fully async for high-performance API responses.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models in app/models/ must inherit from this.
    """
    pass


# ─── Async Engine ─────────────────────────────────────────────────────────────
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,          # Log SQL queries in development
    pool_pre_ping=True,           # Verify connections before use
    pool_size=20,                 # Connection pool size
    max_overflow=10,              # Extra connections allowed beyond pool_size
    pool_recycle=3600,            # Recycle connections after 1 hour
)

# ─── Session Factory ──────────────────────────────────────────────────────────
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # Don't expire objects after commit (async-safe)
    autoflush=False,
    autocommit=False,
)


# ─── Dependency Injection ─────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async DB session per request.
    Automatically closes the session when the request completes.

    Usage:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Utility: Create all tables (for testing/dev) ─────────────────────────────
async def create_all_tables() -> None:
    """
    Creates all tables defined in ORM models.
    Use Alembic migrations in production. This is for dev/test only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables. WARNING: destroys all data. Dev/test only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
