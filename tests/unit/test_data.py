"""
Unit tests for data service.
"""
import pytest
from datetime import date
from src.services.data_service import DataService
from src.schemas.data import DataCreate, DataUpdate, DataFilter
from src.core.exceptions import NotFoundError


class TestDataService:
    """Test cases for DataService."""

    @pytest.mark.asyncio
    async def test_create_data_success(self, db_session, test_client_app, test_strategy):
        """Test successful data creation."""
        data_service = DataService(db_session)
        data_input = DataCreate(
            type="signal",
            symbol="AAPL",
            execute_date=date(2024, 1, 15),
            description="Test signal",
            strategy_id=test_strategy.strategy_id,
            payload={"action": "buy", "quantity": 100}
        )

        data = await data_service.create_data(data_input, test_client_app["client"].id)

        assert data.id is not None
        assert data.type == "signal"
        assert data.symbol == "AAPL"
        assert data.strategy_id == test_strategy.id
        assert data.user_id == test_client_app["client"].id
        assert data.status == "pending"

    @pytest.mark.asyncio
    async def test_create_data_invalid_strategy(self, db_session, test_client_app):
        """Test data creation with invalid strategy."""
        data_service = DataService(db_session)
        data_input = DataCreate(
            type="signal",
            symbol="AAPL",
            execute_date=date(2024, 1, 15),
            strategy_id="nonexistent_strategy"
        )

        with pytest.raises(NotFoundError) as exc_info:
            await data_service.create_data(data_input, test_client_app["client"].id)

        assert "Strategy" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_get_data_by_id(self, db_session, test_client_app, test_strategy):
        """Test getting data by ID."""
        data_service = DataService(db_session)
        data_input = DataCreate(
            type="alert",
            symbol="GOOGL",
            execute_date=date(2024, 1, 16),
            strategy_id=test_strategy.strategy_id
        )

        created = await data_service.create_data(data_input, test_client_app["client"].id)
        fetched = await data_service.get_data_by_id(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.symbol == "GOOGL"

    @pytest.mark.asyncio
    async def test_update_data(self, db_session, test_client_app, test_strategy):
        """Test data update."""
        data_service = DataService(db_session)
        data_input = DataCreate(
            type="signal",
            symbol="MSFT",
            execute_date=date(2024, 1, 17),
            strategy_id=test_strategy.strategy_id,
            description="Original description"
        )

        created = await data_service.create_data(data_input, test_client_app["client"].id)

        update_data = DataUpdate(
            description="Updated description",
            status="processed"
        )

        updated = await data_service.update_data(created.id, update_data)

        assert updated.description == "Updated description"
        assert updated.status == "processed"

    @pytest.mark.asyncio
    async def test_delete_data(self, db_session, test_client_app, test_strategy):
        """Test data deletion."""
        data_service = DataService(db_session)
        data_input = DataCreate(
            type="signal",
            symbol="AMZN",
            execute_date=date(2024, 1, 18),
            strategy_id=test_strategy.strategy_id
        )

        created = await data_service.create_data(data_input, test_client_app["client"].id)

        result = await data_service.delete_data(created.id)
        assert result is True

        # Verify deletion
        fetched = await data_service.get_data_by_id(created.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_list_data_with_filters(self, db_session, test_client_app, test_strategy):
        """Test listing data with filters."""
        data_service = DataService(db_session)

        # Create multiple data records
        for i in range(5):
            data_input = DataCreate(
                type="signal" if i < 3 else "alert",
                symbol=f"SYM{i}",
                execute_date=date(2024, 1, 20 + i),
                strategy_id=test_strategy.strategy_id
            )
            await data_service.create_data(data_input, test_client_app["client"].id)

        # Filter by type
        filters = DataFilter(type="signal", limit=10)
        result = await data_service.list_data(filters, test_client_app["client"].id)

        assert result["total"] == 3
        assert len(result["items"]) == 3

        for item in result["items"]:
            assert item.type == "signal"
