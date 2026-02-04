"""
Unit tests for subscription service.
"""
import pytest
from src.services.subscription_service import SubscriptionService
from src.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionType
from src.core.exceptions import NotFoundError, ValidationError


class TestSubscriptionService:
    """Test cases for SubscriptionService."""

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, db_session, test_client_app, test_strategy):
        """Test successful subscription creation."""
        subscription_service = SubscriptionService(db_session)
        sub_input = SubscriptionCreate(
            name="Test Subscription",
            description="A test subscription",
            subscription_type=SubscriptionType.POLLING,
            strategy_id=test_strategy.strategy_id,
            filters={"type": "signal"}
        )

        subscription = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        assert subscription.id is not None
        assert subscription.name == "Test Subscription"
        assert subscription.subscription_type == "polling"
        assert subscription.strategy_id == test_strategy.id
        assert subscription.client_id == test_client_app["client"].id
        assert subscription.is_active is True

    @pytest.mark.asyncio
    async def test_create_websocket_subscription(self, db_session, test_client_app):
        """Test WebSocket subscription creation."""
        subscription_service = SubscriptionService(db_session)
        sub_input = SubscriptionCreate(
            name="WebSocket Sub",
            subscription_type=SubscriptionType.WEBSOCKET
        )

        subscription = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        assert subscription.subscription_type == "websocket"

    @pytest.mark.asyncio
    async def test_update_subscription(self, db_session, test_client_app):
        """Test subscription update."""
        subscription_service = SubscriptionService(db_session)
        sub_input = SubscriptionCreate(
            name="Original Name",
            description="Original description"
        )

        created = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        update_data = SubscriptionUpdate(
            name="Updated Name",
            is_active=False
        )

        updated = await subscription_service.update_subscription(
            created.id, update_data, test_client_app["client"].id
        )

        assert updated.name == "Updated Name"
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_update_subscription_wrong_client(self, db_session, test_client_app):
        """Test that clients can only update their own subscriptions."""
        subscription_service = SubscriptionService(db_session)
        sub_input = SubscriptionCreate(name="My Subscription")

        created = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        update_data = SubscriptionUpdate(name="Hacked Name")

        with pytest.raises(ValidationError):
            await subscription_service.update_subscription(
                created.id, update_data, client_id=99999  # Wrong client
            )

    @pytest.mark.asyncio
    async def test_delete_subscription(self, db_session, test_client_app):
        """Test subscription deletion."""
        subscription_service = SubscriptionService(db_session)
        sub_input = SubscriptionCreate(name="To Delete")

        created = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        result = await subscription_service.delete_subscription(
            created.id, test_client_app["client"].id
        )

        assert result is True

        # Verify deletion
        fetched = await subscription_service.get_subscription_by_id(created.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, db_session, test_client_app):
        """Test listing subscriptions."""
        subscription_service = SubscriptionService(db_session)

        # Create multiple subscriptions
        for i in range(3):
            sub_input = SubscriptionCreate(name=f"Subscription {i}")
            await subscription_service.create_subscription(
                sub_input, test_client_app["client"].id
            )

        result = await subscription_service.list_subscriptions(
            test_client_app["client"].id
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3

    @pytest.mark.asyncio
    async def test_get_subscription_data(self, db_session, test_client_app, test_strategy):
        """Test getting subscription data."""
        from src.services.data_service import DataService
        from src.schemas.data import DataCreate
        from datetime import date

        subscription_service = SubscriptionService(db_session)
        data_service = DataService(db_session)

        # Create subscription
        sub_input = SubscriptionCreate(
            name="Data Subscription",
            strategy_id=test_strategy.strategy_id
        )
        subscription = await subscription_service.create_subscription(
            sub_input, test_client_app["client"].id
        )

        # Create some data
        for i in range(3):
            data_input = DataCreate(
                type="signal",
                symbol=f"SYM{i}",
                execute_date=date(2024, 2, 1 + i),
                strategy_id=test_strategy.strategy_id
            )
            await data_service.create_data(data_input, test_client_app["client"].id)

        # Get subscription data
        result = await subscription_service.get_subscription_data(
            subscription.id, test_client_app["client"].id
        )

        assert result["subscription_id"] == subscription.id
        assert len(result["data"]) == 3
        assert result["has_more"] is False
