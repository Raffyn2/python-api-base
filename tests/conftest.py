"""Pytest configuration and shared fixtures."""

import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from my_api.domain.entities.item import Item, ItemCreate, ItemUpdate
from my_api.infrastructure.database.session import DatabaseSession


# Test database URL - uses Docker PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/my_api_test"
)


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[DatabaseSession, None]:
    """Create a database session for testing.
    
    Creates tables before each test and drops them after.
    """
    db = DatabaseSession(
        database_url=TEST_DATABASE_URL,
        pool_size=2,
        max_overflow=5,
        echo=False,
    )
    
    # Create tables
    await db.create_tables()
    
    yield db
    
    # Drop tables after test
    await db.drop_tables()
    await db.close()


@pytest_asyncio.fixture(scope="function")
async def async_session(db_session: DatabaseSession) -> AsyncGenerator[AsyncSession, None]:
    """Get an async session from the database session manager."""
    async with db_session.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for API testing."""
    from my_api.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_item_data() -> dict[str, Any]:
    """Sample item data for testing."""
    return {
        "name": "Test Item",
        "description": "A test item description",
        "price": 29.99,
        "tax": 2.40,
    }


@pytest.fixture
def sample_item_create() -> ItemCreate:
    """Sample ItemCreate DTO."""
    return ItemCreate(
        name="Test Item",
        description="A test item description",
        price=29.99,
        tax=2.40,
    )


@pytest.fixture
def sample_item_update() -> ItemUpdate:
    """Sample ItemUpdate DTO."""
    return ItemUpdate(
        name="Updated Item",
        price=39.99,
    )
