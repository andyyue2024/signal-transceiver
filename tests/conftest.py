"""
Pytest configuration and fixtures.
"""
import os
import sys
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import Base, get_db
from src.main import app


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_maker() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from src.services.auth_service import AuthService
    from src.schemas.user import UserCreate

    auth_service = AuthService(db_session)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    user, api_key = await auth_service.register_user(user_data)

    return {"user": user, "api_key": api_key}


@pytest_asyncio.fixture
async def test_client_app(db_session: AsyncSession, test_user):
    """Create a test client application."""
    from src.services.client_service import ClientService
    from src.schemas.client import ClientCreate

    client_service = ClientService(db_session)
    client_data = ClientCreate(
        name="Test Client",
        description="Test client application"
    )
    client, client_secret = await client_service.create_client(
        client_data, test_user["user"].id
    )

    return {
        "client": client,
        "client_key": client.client_key,
        "client_secret": client_secret
    }


@pytest_asyncio.fixture
async def test_strategy(db_session: AsyncSession):
    """Create a test strategy."""
    from src.services.strategy_service import StrategyService
    from src.schemas.strategy import StrategyCreate

    strategy_service = StrategyService(db_session)
    strategy_data = StrategyCreate(
        strategy_id="test_strategy_001",
        name="Test Strategy",
        description="A test strategy",
        type="default"
    )
    strategy = await strategy_service.create_strategy(strategy_data)

    return strategy


@pytest_asyncio.fixture
async def admin_api_key():
    """Get admin API key from settings."""
    from src.config.settings import settings
    return settings.admin_api_key
