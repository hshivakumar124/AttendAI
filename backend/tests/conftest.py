"""
AttendAI — Test Configuration & Fixtures
==========================================
Uses async in-memory SQLite for all tests.
The async session matches production (asyncpg/PostgreSQL) behavior.
No PostgreSQL required to run the test suite.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app

# ─── Async In-Memory SQLite for Testing ──────────────────────────────────────
SQLITE_ASYNC_URL = "sqlite+aiosqlite://"   # In-memory, fully async

async_engine = create_async_engine(
    SQLITE_ASYNC_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

AsyncTestingSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def override_get_db():
    """Async DB override using in-memory SQLite."""
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Session-scoped DB setup ──────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db(event_loop):
    """Create all tables in async SQLite before tests run."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await async_engine.dispose()


# ─── Per-test client fixture ──────────────────────────────────────────────────
@pytest.fixture
def client():
    """TestClient with async SQLite DB override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
