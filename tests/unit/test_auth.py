"""
Unit tests for authentication service.
"""
import pytest
from src.services.auth_service import AuthService
from src.schemas.user import UserCreate
from src.core.exceptions import AuthenticationError, ConflictError


class TestAuthService:
    """Test cases for AuthService."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session):
        """Test successful user registration."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            full_name="New User"
        )

        user, api_key = await auth_service.register_user(user_data)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_admin is False
        assert api_key.startswith("sk_")

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, db_session):
        """Test registration with duplicate username."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="duplicateuser",
            email="user1@example.com",
            password="password123"
        )

        await auth_service.register_user(user_data)

        # Try to register with same username
        user_data2 = UserCreate(
            username="duplicateuser",
            email="user2@example.com",
            password="password123"
        )

        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register_user(user_data2)

        assert "already exists" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session):
        """Test successful user authentication."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="authuser",
            email="authuser@example.com",
            password="mypassword"
        )

        await auth_service.register_user(user_data)

        authenticated_user = await auth_service.authenticate_user("authuser", "mypassword")

        assert authenticated_user.username == "authuser"
        assert authenticated_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="wrongpassuser",
            email="wrongpass@example.com",
            password="correctpassword"
        )

        await auth_service.register_user(user_data)

        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user("wrongpassuser", "wrongpassword")

    @pytest.mark.asyncio
    async def test_regenerate_api_key(self, db_session):
        """Test API key regeneration."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="regenuser",
            email="regen@example.com",
            password="password123"
        )

        user, old_api_key = await auth_service.register_user(user_data)

        new_api_key = await auth_service.regenerate_api_key(user.id, expires_in_days=30)

        assert new_api_key != old_api_key
        assert new_api_key.startswith("sk_")

    @pytest.mark.asyncio
    async def test_update_password(self, db_session):
        """Test password update."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            username="updatepassuser",
            email="updatepass@example.com",
            password="oldpassword"
        )

        user, _ = await auth_service.register_user(user_data)

        result = await auth_service.update_password(user.id, "oldpassword", "newpassword")

        assert result is True

        # Verify new password works
        authenticated = await auth_service.authenticate_user("updatepassuser", "newpassword")
        assert authenticated.id == user.id
