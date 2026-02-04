"""
Client service for managing client applications.
Now uses the unified User model - clients and users are the same entity.
"""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.client import ClientCreate, ClientUpdate
from src.core.security import generate_client_credentials, generate_api_key, get_password_hash
from src.core.exceptions import NotFoundError, ConflictError


class ClientService:
    """
    Service for client operations.
    Note: Client and User are now unified - this service manages Users with client credentials.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_client(
        self, client_input: ClientCreate, owner_id: Optional[int] = None
    ) -> Tuple[User, str]:
        """
        Create a new client (user with client credentials).

        Args:
            client_input: Client creation data (includes username, email, password)
            owner_id: Optional owner_id (deprecated, kept for compatibility)

        Returns:
            Tuple of (User, client_secret) - secret is only returned once
        """
        # Check if username or email already exists
        existing = await self.db.execute(
            select(User).where(
                (User.username == client_input.name) | (User.email == client_input.email)
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User with this username or email already exists")

        # Generate client credentials
        client_key, client_secret, hashed_secret = generate_client_credentials()

        # Generate API key for web UI access
        api_key, hashed_api_key = generate_api_key()

        # Hash password
        hashed_password = get_password_hash(client_input.password)

        # Create user with client credentials
        user = User(
            username=client_input.name,
            email=client_input.email,
            hashed_password=hashed_password,
            api_key=hashed_api_key,
            client_key=client_key,
            client_secret=hashed_secret,
            description=client_input.description,
            contact_email=client_input.contact_email,
            phone=client_input.phone,
            webhook_url=client_input.webhook_url,
            rate_limit=client_input.rate_limit,
            is_active=True,
            is_admin=False
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Return plain text secret (only time it's visible)
        return user, client_secret

    async def get_client_by_id(self, client_id: int) -> Optional[User]:
        """Get client (user) by ID."""
        result = await self.db.execute(
            select(User).where(User.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_client_by_key(self, client_key: str) -> Optional[User]:
        """Get client (user) by client key."""
        result = await self.db.execute(
            select(User).where(User.client_key == client_key)
        )
        return result.scalar_one_or_none()

    async def update_client(
        self, client_id: int, update_data: ClientUpdate, owner_id: Optional[int] = None
    ) -> User:
        """
        Update a client (user).

        Args:
            client_id: User ID
            update_data: Update data
            owner_id: Deprecated (kept for compatibility)
        """
        user = await self.get_client_by_id(client_id)

        if not user:
            raise NotFoundError("Client", client_id)

        # Update allowed fields
        update_dict = update_data.model_dump(exclude_unset=True)

        # Map client fields to user fields
        field_mapping = {
            'name': 'username',
            'contact_phone': 'phone'
        }

        for key, value in update_dict.items():
            # Map field names
            user_field = field_mapping.get(key, key)
            if hasattr(user, user_field):
                setattr(user, user_field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_client(self, client_id: int, owner_id: Optional[int] = None) -> bool:
        """
        Delete a client (user).

        Args:
            client_id: User ID
            owner_id: Deprecated (kept for compatibility)
        """
        user = await self.get_client_by_id(client_id)

        if not user:
            raise NotFoundError("Client", client_id)

        await self.db.delete(user)
        await self.db.commit()

        return True

    async def list_clients(
        self, owner_id: Optional[int] = None, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        List clients (users).

        Args:
            owner_id: Deprecated (kept for compatibility), now lists all users
            limit: Maximum number of results
            offset: Offset for pagination
        """
        query = select(User).where(User.is_active == True)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Get total count
        count_query = select(User).where(User.is_active == True)
        count_result = await self.db.execute(count_query)
        total = len(list(count_result.scalars().all()))

        return {
            "total": total,
            "items": items
        }

    async def regenerate_credentials(
        self, client_id: int, owner_id: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Regenerate client credentials.

        Args:
            client_id: User ID
            owner_id: Deprecated (kept for compatibility)

        Returns:
            Tuple of (client_key, client_secret)
        """
        user = await self.get_client_by_id(client_id)

        if not user:
            raise NotFoundError("Client", client_id)

        # Generate new credentials
        client_key, client_secret, hashed_secret = generate_client_credentials()

        user.client_key = client_key
        user.client_secret = hashed_secret
        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return client_key, client_secret

    async def update_last_access(self, client_id: int) -> None:
        """Update last access time for a client (user)."""
        user = await self.get_client_by_id(client_id)
        if user:
            user.last_access_at = datetime.utcnow()
            await self.db.commit()
