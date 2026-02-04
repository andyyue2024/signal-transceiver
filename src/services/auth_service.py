"""
Authentication service for user and API key management.
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import UserCreate
from src.core.security import (
    generate_api_key, hash_api_key, get_password_hash,
    verify_password, calculate_expiry, generate_client_credentials
)
from src.core.exceptions import (
    AuthenticationError, ConflictError, NotFoundError
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> Tuple[User, str]:
        """
        Register a new user.

        Returns:
            Tuple of (User, api_key)
        """
        # Check if username exists
        existing = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Username '{user_data.username}' already exists")

        # Check if email exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email '{user_data.email}' already registered")

        # Generate API key
        api_key, hashed_key = generate_api_key()

        # Generate client credentials
        client_key, client_secret, hashed_secret = generate_client_credentials()

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            api_key=hashed_key,
            api_key_expires_at=calculate_expiry(days=365),
            client_key=client_key,
            client_secret=hashed_secret,
            full_name=user_data.full_name,
            phone=user_data.phone,
            is_active=True,
            is_admin=False
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user, api_key

    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user with username and password."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("Invalid username or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        return user

    async def regenerate_api_key(self, user_id: int, expires_in_days: int = 365) -> str:
        """Regenerate API key for a user."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User", user_id)

        # Generate new API key
        api_key, hashed_key = generate_api_key()

        user.api_key = hashed_key
        user.api_key_expires_at = calculate_expiry(days=expires_in_days)

        await self.db.commit()

        return api_key

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Update user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

        return True
