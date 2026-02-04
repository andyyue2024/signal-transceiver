"""
Tests for Data Import Service
"""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.config.database import Base
from src.services.import_service import DataImportService
from src.models.strategy import Strategy
from src.models.user import User
from src.core.security import generate_api_key, generate_client_credentials, get_password_hash


@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user"""
    api_key, hashed_key = generate_api_key()
    client_key, client_secret, hashed_secret = generate_client_credentials()

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        api_key=hashed_key,
        client_key=client_key,
        client_secret=hashed_secret,
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_strategy(db_session, test_user):
    """Create test strategy"""
    strategy = Strategy(
        name="Test Strategy",
        description="Test strategy for import",
        type="trading",
        user_id=test_user.id,
        is_active=True
    )
    db_session.add(strategy)
    await db_session.commit()
    await db_session.refresh(strategy)
    return strategy


class TestDataImportService:
    """Test data import service"""

    @pytest.mark.asyncio
    async def test_import_from_csv(self, db_session, test_user, test_strategy):
        """Test importing from CSV"""
        csv_content = f"""type,strategy_id,symbol,execute_date,description,metadata
signal,{test_strategy.id},AAPL,2024-01-01,Buy signal,"{{\\"price\\": 150.0}}"
data,{test_strategy.id},GOOGL,2024-01-02,Market data,"{{\\"volume\\": 1000000}}"
"""

        service = DataImportService(db_session)
        result = await service.import_from_csv(csv_content, test_user.id)

        assert result.total == 2
        assert result.success == 2
        assert result.failed == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_from_csv_with_errors(self, db_session, test_user):
        """Test CSV import with invalid data"""
        csv_content = """type,strategy_id,symbol,execute_date,description,metadata
signal,999,AAPL,2024-01-01,Buy signal,{}
invalid,,GOOGL,2024-01-02,Invalid,{}
"""

        service = DataImportService(db_session)
        result = await service.import_from_csv(csv_content, test_user.id, skip_errors=True)

        assert result.total == 2
        assert result.success == 0
        assert result.failed == 2
        assert len(result.errors) == 2

    @pytest.mark.asyncio
    async def test_import_from_json(self, db_session, test_user, test_strategy):
        """Test importing from JSON"""
        json_data = [
            {
                "type": "signal",
                "strategy_id": test_strategy.id,
                "symbol": "AAPL",
                "execute_date": "2024-01-01",
                "description": "Buy signal",
                "metadata": {"price": 150.0}
            },
            {
                "type": "data",
                "strategy_id": test_strategy.id,
                "symbol": "GOOGL",
                "execute_date": "2024-01-02",
                "description": "Market data",
                "metadata": {"volume": 1000000}
            }
        ]

        service = DataImportService(db_session)
        result = await service.import_from_json(json_data, test_user.id)

        assert result.total == 2
        assert result.success == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_import_from_json_with_errors(self, db_session, test_user):
        """Test JSON import with invalid data"""
        json_data = [
            {
                "type": "signal",
                "strategy_id": 999,  # Non-existent strategy
                "symbol": "AAPL"
            },
            {
                "type": "invalid",
                # Missing required fields
            }
        ]

        service = DataImportService(db_session)
        result = await service.import_from_json(json_data, test_user.id, skip_errors=True)

        assert result.total == 2
        assert result.failed == 2

    @pytest.mark.asyncio
    async def test_validate_import_data(self, db_session):
        """Test data validation"""
        valid_data = [
            {
                "type": "signal",
                "strategy_id": 1,
                "symbol": "AAPL",
                "execute_date": "2024-01-01"
            }
        ]

        service = DataImportService(db_session)
        result = await service.validate_import_data(valid_data)

        assert result["total"] == 1
        assert result["valid"] == 1
        assert result["invalid"] == 0
        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_import_data_with_errors(self, db_session):
        """Test validation with invalid data"""
        invalid_data = [
            {
                "type": "signal",
                # Missing strategy_id and symbol
            },
            {
                "strategy_id": "invalid",  # Should be integer
                "symbol": "AAPL"
            }
        ]

        service = DataImportService(db_session)
        result = await service.validate_import_data(invalid_data)

        assert result["total"] == 2
        assert result["valid"] == 0
        assert result["invalid"] == 2
        assert result["is_valid"] is False
        assert len(result["errors"]) == 2
