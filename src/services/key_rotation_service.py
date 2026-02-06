"""
API Key rotation and management service.
Handles API key lifecycle including expiry notifications.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.user import User
from src.core.security import generate_api_key, generate_client_credentials, hash_api_key


@dataclass
class KeyExpiryInfo:
    """Information about a key nearing expiration."""
    entity_type: str  # 'user_api_key' or 'user_client_secret'
    entity_id: int
    entity_name: str
    expires_at: datetime
    days_remaining: int
    email: Optional[str] = None


class KeyRotationService:
    """Service for managing API key rotation and expiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_expiring_keys(self, warning_days: int = 30) -> List[KeyExpiryInfo]:
        """
        Check for keys that will expire soon.

        Args:
            warning_days: Number of days before expiry to warn

        Returns:
            List of expiring key information
        """
        expiring = []
        now = datetime.utcnow()
        warning_threshold = now + timedelta(days=warning_days)

        # Check user API keys
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.api_key_expires_at != None,
                    User.api_key_expires_at <= warning_threshold,
                    User.api_key_expires_at > now,
                    User.is_active == True
                )
            )
        )
        users = user_result.scalars().all()

        for user in users:
            days_remaining = (user.api_key_expires_at - now).days
            expiring.append(KeyExpiryInfo(
                entity_type="user_api_key",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.api_key_expires_at,
                days_remaining=days_remaining,
                email=user.email
            ))

        # Check user client secret keys
        secret_result = await self.db.execute(
            select(User).where(
                and_(
                    User.secret_expires_at != None,
                    User.secret_expires_at <= warning_threshold,
                    User.secret_expires_at > now,
                    User.is_active == True
                )
            )
        )
        users_with_secrets = secret_result.scalars().all()

        for user in users_with_secrets:
            days_remaining = (user.secret_expires_at - now).days
            expiring.append(KeyExpiryInfo(
                entity_type="user_client_secret",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.secret_expires_at,
                days_remaining=days_remaining,
                email=user.email
            ))

        # Sort by days remaining
        expiring.sort(key=lambda x: x.days_remaining)

        return expiring

    async def check_expired_keys(self) -> List[KeyExpiryInfo]:
        """Check for already expired keys."""
        expired = []
        now = datetime.utcnow()

        # Check expired user API keys
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.api_key_expires_at != None,
                    User.api_key_expires_at <= now,
                    User.is_active == True
                )
            )
        )
        users = user_result.scalars().all()

        for user in users:
            days_expired = (now - user.api_key_expires_at).days
            expired.append(KeyExpiryInfo(
                entity_type="user_api_key",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.api_key_expires_at,
                days_remaining=-days_expired,
                email=user.email
            ))

        # Check expired user client secret keys
        secret_result = await self.db.execute(
            select(User).where(
                and_(
                    User.secret_expires_at != None,
                    User.secret_expires_at <= now,
                    User.is_active == True
                )
            )
        )
        users_with_secrets = secret_result.scalars().all()

        for user in users_with_secrets:
            days_expired = (now - user.secret_expires_at).days
            expired.append(KeyExpiryInfo(
                entity_type="user_client_secret",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.secret_expires_at,
                days_remaining=-days_expired,
                email=user.email
            ))

        return expired

    async def rotate_user_key(
        self,
        user_id: int,
        expiry_days: int = 365
    ) -> tuple[str, datetime]:
        """
        Rotate a user's API key.

        Args:
            user_id: User ID
            expiry_days: Days until new key expires

        Returns:
            Tuple of (new_api_key, expires_at)
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generate new key
        new_key, hashed_key = generate_api_key()
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Update user
        user.api_key = hashed_key
        user.api_key_expires_at = expires_at
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Rotated API key for user {user.username}")

        return new_key, expires_at

    async def rotate_client_secret(
        self,
        user_id: int,
        expiry_days: int = 365
    ) -> tuple[str, str, datetime]:
        """
        Rotate a user's client secret.

        Args:
            user_id: User ID
            expiry_days: Days until new secret expires

        Returns:
            Tuple of (client_key, new_secret, expires_at)
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generate new credentials
        _, new_secret, hashed_secret = generate_client_credentials()
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Update user
        user.client_secret = hashed_secret
        user.secret_expires_at = expires_at
        user.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Rotated client secret for user {user.username}")

        return user.client_key, new_secret, expires_at

    async def get_key_stats(self) -> Dict[str, Any]:
        """Get statistics about API keys."""
        now = datetime.utcnow()

        # User API keys stats
        total_users = (await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )).scalar() or 0

        users_with_api_key_expiry = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.is_active == True, User.api_key_expires_at != None)
            )
        )).scalar() or 0

        expired_api_keys = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    User.api_key_expires_at != None,
                    User.api_key_expires_at <= now
                )
            )
        )).scalar() or 0

        # User client secret stats
        users_with_secret_expiry = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.is_active == True, User.secret_expires_at != None)
            )
        )).scalar() or 0

        expired_secrets = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    User.secret_expires_at != None,
                    User.secret_expires_at <= now
                )
            )
        )).scalar() or 0

        return {
            "users": {
                "total": total_users,
                "api_keys": {
                    "with_expiry": users_with_api_key_expiry,
                    "expired": expired_api_keys
                },
                "client_secrets": {
                    "with_expiry": users_with_secret_expiry,
                    "expired": expired_secrets
                }
            },
            "checked_at": now.isoformat()
        }

