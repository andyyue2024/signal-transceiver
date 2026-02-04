"""
API Key rotation and management service.
Handles API key lifecycle including expiry notifications.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.user import User
from src.models.client import Client
from src.core.security import generate_api_key, generate_client_credentials, hash_api_key


@dataclass
class KeyExpiryInfo:
    """Information about a key nearing expiration."""
    entity_type: str  # 'user' or 'client'
    entity_id: int
    entity_name: str
    expires_at: datetime
    days_remaining: int
    email: Optional[str] = None


class KeyRotationService:
    """Service for managing API key rotation and expiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_expiring_keys(
        self,
        warning_days: int = 30
    ) -> List[KeyExpiryInfo]:
        """
        Check for keys that are expiring soon.

        Args:
            warning_days: Number of days before expiry to warn

        Returns:
            List of keys nearing expiration
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
                entity_type="user",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.api_key_expires_at,
                days_remaining=days_remaining,
                email=user.email
            ))

        # Check client keys
        client_result = await self.db.execute(
            select(Client).where(
                and_(
                    Client.secret_expires_at != None,
                    Client.secret_expires_at <= warning_threshold,
                    Client.secret_expires_at > now,
                    Client.is_active == True
                )
            )
        )
        clients = client_result.scalars().all()

        for client in clients:
            days_remaining = (client.secret_expires_at - now).days
            expiring.append(KeyExpiryInfo(
                entity_type="client",
                entity_id=client.id,
                entity_name=client.name,
                expires_at=client.secret_expires_at,
                days_remaining=days_remaining,
                email=client.contact_email
            ))

        # Sort by days remaining
        expiring.sort(key=lambda x: x.days_remaining)

        return expiring

    async def check_expired_keys(self) -> List[KeyExpiryInfo]:
        """Check for already expired keys."""
        expired = []
        now = datetime.utcnow()

        # Check expired user keys
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
                entity_type="user",
                entity_id=user.id,
                entity_name=user.username,
                expires_at=user.api_key_expires_at,
                days_remaining=-days_expired,
                email=user.email
            ))

        # Check expired client keys
        client_result = await self.db.execute(
            select(Client).where(
                and_(
                    Client.secret_expires_at != None,
                    Client.secret_expires_at <= now,
                    Client.is_active == True
                )
            )
        )
        clients = client_result.scalars().all()

        for client in clients:
            days_expired = (now - client.secret_expires_at).days
            expired.append(KeyExpiryInfo(
                entity_type="client",
                entity_id=client.id,
                entity_name=client.name,
                expires_at=client.secret_expires_at,
                days_remaining=-days_expired,
                email=client.contact_email
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
        client_id: int,
        expiry_days: int = 365
    ) -> tuple[str, str, datetime]:
        """
        Rotate a client's secret.

        Args:
            client_id: Client ID
            expiry_days: Days until new secret expires

        Returns:
            Tuple of (client_key, new_secret, expires_at)
        """
        client = await self.db.get(Client, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Generate new credentials
        _, new_secret, hashed_secret = generate_client_credentials()
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Update client
        client.client_secret = hashed_secret
        client.secret_expires_at = expires_at
        client.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Rotated secret for client {client.name}")

        return client.client_key, new_secret, expires_at

    async def get_key_stats(self) -> Dict[str, Any]:
        """Get statistics about API keys."""
        now = datetime.utcnow()

        # User keys
        total_users = (await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )).scalar() or 0

        users_with_expiry = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.is_active == True, User.api_key_expires_at != None)
            )
        )).scalar() or 0

        expired_users = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(
                    User.is_active == True,
                    User.api_key_expires_at != None,
                    User.api_key_expires_at <= now
                )
            )
        )).scalar() or 0

        # Client keys
        total_clients = (await self.db.execute(
            select(func.count(Client.id)).where(Client.is_active == True)
        )).scalar() or 0

        clients_with_expiry = (await self.db.execute(
            select(func.count(Client.id)).where(
                and_(Client.is_active == True, Client.secret_expires_at != None)
            )
        )).scalar() or 0

        expired_clients = (await self.db.execute(
            select(func.count(Client.id)).where(
                and_(
                    Client.is_active == True,
                    Client.secret_expires_at != None,
                    Client.secret_expires_at <= now
                )
            )
        )).scalar() or 0

        return {
            "users": {
                "total": total_users,
                "with_expiry": users_with_expiry,
                "expired": expired_users
            },
            "clients": {
                "total": total_clients,
                "with_expiry": clients_with_expiry,
                "expired": expired_clients
            },
            "checked_at": now.isoformat()
        }


# Import at top to avoid circular imports
from sqlalchemy import func
