"""Shared pytest fixtures."""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Use SQLite for tests (no Postgres required)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("DB__POSTGRES_URL", TEST_DB_URL)
os.environ.setdefault("DB__REDIS_URL", "redis://localhost:6379/15")


def _patch_jsonb_for_sqlite(metadata) -> None:
    """Replace JSONB columns with JSON so SQLite can create the schema."""
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import String

    for table in metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    from cati.db.engine import Base
    import cati.survey.models  # noqa: F401 — registers all ORM models with Base.metadata
    _patch_jsonb_for_sqlite(Base.metadata)
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with overridden DB session."""
    from cati.api.app import create_app
    from cati.api.dependencies import db_session as dep_db_session
    from sqlalchemy.ext.asyncio import async_sessionmaker

    app = create_app()
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_db_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[dep_db_session] = override_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": "test-key"},
    ) as ac:
        yield ac
