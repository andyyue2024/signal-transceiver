"""
FastAPI dependencies for authentication and authorization.
"""
from datetime import datetime
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.settings import settings
from src.models.user import User
from src.models.client import Client
from src.models.permission import ClientPermission, Role
from src.core.security import hash_api_key, is_expired
from src.core.exceptions import AuthenticationError, AuthorizationError

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from API key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Check for admin key
    if api_key == settings.admin_api_key:
        # Return a virtual admin user
        admin_user = User(
            id=0,
            username="admin",
            email="admin@system.local",
            hashed_password="",
            api_key="admin",
            is_active=True,
            is_admin=True
        )
        return admin_user

    # Hash the API key for comparison
    hashed_key = hash_api_key(api_key)

    # Find user by API key
    result = await db.execute(
        select(User).where(User.api_key == hashed_key)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    if is_expired(user.api_key_expires_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_client_from_key(
    x_client_key: Optional[str] = Header(None),
    x_client_secret: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Client:
    """
    Dependency to authenticate and get client from client credentials.
    """
    if not x_client_key or not x_client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client credentials required (X-Client-Key and X-Client-Secret headers)"
        )

    # Find client by key
    result = await db.execute(
        select(Client).where(Client.client_key == x_client_key)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )

    # Verify secret
    hashed_secret = hash_api_key(x_client_secret)
    if client.client_secret != hashed_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )

    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client is disabled"
        )

    # Update last access
    client.last_access_at = datetime.utcnow()
    await db.commit()

    return client


class PermissionChecker:
    """Dependency class for checking permissions."""

    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        client: Client = Depends(get_client_from_key),
        db: AsyncSession = Depends(get_db)
    ) -> Client:
        """Check if client has required permissions."""
        # Get client's permissions through roles
        result = await db.execute(
            select(ClientPermission)
            .where(ClientPermission.client_id == client.id)
            .where(ClientPermission.is_active == True)
        )
        client_permissions = result.scalars().all()

        # Collect all permission codes
        permission_codes = set()
        for cp in client_permissions:
            if cp.role and cp.role.permissions:
                for perm in cp.role.permissions:
                    permission_codes.add(perm.code)

        # Check required permissions
        for required in self.required_permissions:
            if required not in permission_codes:
                raise AuthorizationError(
                    f"Permission '{required}' is required",
                    details={"required": required, "available": list(permission_codes)}
                )

        return client


def require_permissions(*permissions: str):
    """Factory function to create permission checker dependency."""
    return PermissionChecker(list(permissions))
