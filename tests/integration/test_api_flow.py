"""
Integration tests for API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration via API."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "apiuser",
                "email": "apiuser@example.com",
                "password": "securepassword123",
                "full_name": "API User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data["data"]
        assert data["data"]["user"]["username"] == "apiuser"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "first@example.com",
                "password": "password123"
            }
        )

        # Second registration with same username
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "second@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "mypassword"
            }
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "mypassword"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_me_with_api_key(self, client: AsyncClient, test_user):
        """Test getting current user with API key."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": test_user["api_key"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_me_without_api_key(self, client: AsyncClient):
        """Test getting current user without API key."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestClientAPI:
    """Test client management API endpoints."""

    @pytest.mark.asyncio
    async def test_create_client(self, client: AsyncClient, test_user):
        """Test client creation."""
        response = await client.post(
            "/api/v1/clients",
            json={
                "name": "My Client App",
                "description": "Test client application"
            },
            headers={"X-API-Key": test_user["api_key"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Client App"
        assert "client_key" in data
        assert "client_secret" in data

    @pytest.mark.asyncio
    async def test_list_clients(self, client: AsyncClient, test_user, test_client_app):
        """Test listing clients."""
        response = await client.get(
            "/api/v1/clients",
            headers={"X-API-Key": test_user["api_key"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestDataAPI:
    """Test data API endpoints."""

    @pytest.mark.asyncio
    async def test_create_data(self, client: AsyncClient, test_client_app, test_strategy):
        """Test data creation."""
        response = await client.post(
            "/api/v1/data",
            json={
                "type": "signal",
                "symbol": "AAPL",
                "execute_date": "2024-02-01",
                "strategy_id": test_strategy.strategy_id,
                "description": "Buy signal"
            },
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "signal"
        assert data["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_list_data(self, client: AsyncClient, test_client_app, test_strategy):
        """Test listing data."""
        # Create some data first
        await client.post(
            "/api/v1/data",
            json={
                "type": "signal",
                "symbol": "GOOGL",
                "execute_date": "2024-02-02",
                "strategy_id": test_strategy.strategy_id
            },
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )

        # List data
        response = await client.get(
            "/api/v1/data",
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data


class TestSubscriptionAPI:
    """Test subscription API endpoints."""

    @pytest.mark.asyncio
    async def test_create_subscription(self, client: AsyncClient, test_client_app, test_strategy):
        """Test subscription creation."""
        response = await client.post(
            "/api/v1/subscriptions",
            json={
                "name": "My Subscription",
                "subscription_type": "polling",
                "strategy_id": test_strategy.strategy_id
            },
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Subscription"
        assert data["subscription_type"] == "polling"

    @pytest.mark.asyncio
    async def test_get_subscription_data(self, client: AsyncClient, test_client_app, test_strategy):
        """Test getting subscription data."""
        # Create subscription
        sub_response = await client.post(
            "/api/v1/subscriptions",
            json={
                "name": "Data Subscription",
                "strategy_id": test_strategy.strategy_id
            },
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )
        subscription_id = sub_response.json()["id"]

        # Get subscription data
        response = await client.get(
            f"/api/v1/subscriptions/{subscription_id}/data",
            headers={
                "X-Client-Key": test_client_app["client_key"],
                "X-Client-Secret": test_client_app["client_secret"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "subscription_id" in data
        assert "data" in data


class TestStrategyAPI:
    """Test strategy API endpoints."""

    @pytest.mark.asyncio
    async def test_create_strategy_as_admin(self, client: AsyncClient, admin_api_key):
        """Test strategy creation as admin."""
        response = await client.post(
            "/api/v1/strategies",
            json={
                "strategy_id": "new_strategy",
                "name": "New Strategy",
                "type": "momentum",
                "description": "A new trading strategy"
            },
            headers={"X-API-Key": admin_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "new_strategy"
        assert data["name"] == "New Strategy"

    @pytest.mark.asyncio
    async def test_list_strategies(self, client: AsyncClient, test_user, test_strategy):
        """Test listing strategies."""
        response = await client.get(
            "/api/v1/strategies",
            headers={"X-API-Key": test_user["api_key"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestAdminAPI:
    """Test admin API endpoints."""

    @pytest.mark.asyncio
    async def test_init_permissions(self, client: AsyncClient, admin_api_key):
        """Test initializing default permissions."""
        response = await client.post(
            "/api/v1/admin/init-permissions",
            headers={"X-API-Key": admin_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_permissions(self, client: AsyncClient, admin_api_key):
        """Test listing permissions."""
        # Init first
        await client.post(
            "/api/v1/admin/init-permissions",
            headers={"X-API-Key": admin_api_key}
        )

        response = await client.get(
            "/api/v1/admin/permissions",
            headers={"X-API-Key": admin_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    @pytest.mark.asyncio
    async def test_admin_access_denied_for_regular_user(self, client: AsyncClient, test_user):
        """Test that regular users cannot access admin endpoints."""
        response = await client.get(
            "/api/v1/admin/permissions",
            headers={"X-API-Key": test_user["api_key"]}
        )

        assert response.status_code == 403
