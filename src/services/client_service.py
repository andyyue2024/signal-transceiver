"""
Client service for managing client applications.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client import Client
from src.models.user import User
from src.schemas.client import ClientCreate, ClientUpdate
from src.core.security import generate_client_credentials
from src.core.exceptions import NotFoundError, ConflictError


class ClientService:
    """Service for client operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_client(
        self, client_input: ClientCreate, owner_id: int
    ) -> Tuple[Client, str]:
        """
        Create a new client.

        Returns:
            Tuple of (Client, client_secret) - secret is only returned once
        """
        # Generate client credentials
        client_key, client_secret, hashed_secret = generate_client_credentials()

        # Create client
        client = Client(
            name=client_input.name,
            client_key=client_key,
            client_secret=hashed_secret,
            owner_id=owner_id,
            description=client_input.description,
            contact_email=client_input.contact_email,
            contact_phone=client_input.contact_phone,
            webhook_url=client_input.webhook_url,
            rate_limit=client_input.rate_limit,
            is_active=True
        )

        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client, client_secret

    async def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Get client by ID."""
        result = await self.db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_client_by_key(self, client_key: str) -> Optional[Client]:
        """Get client by client key."""
        result = await self.db.execute(
            select(Client).where(Client.client_key == client_key)
        )
        return result.scalar_one_or_none()

    async def update_client(
        self, client_id: int, update_data: ClientUpdate, owner_id: int
    ) -> Client:
        """Update a client."""
        client = await self.get_client_by_id(client_id)

        if not client:
            raise NotFoundError("Client", client_id)

        if client.owner_id != owner_id:
            raise NotFoundError("Client", client_id)  # Hide existence for security

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(client, key, value)

        client.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def delete_client(self, client_id: int, owner_id: int) -> bool:
        """Delete a client."""
        client = await self.get_client_by_id(client_id)

        if not client:
            raise NotFoundError("Client", client_id)

        if client.owner_id != owner_id:
            raise NotFoundError("Client", client_id)

        await self.db.delete(client)
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

