"""
Client management API endpoints.
Note: Client and User are now unified. These endpoints manage Users with client credentials.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse,
    ClientWithSecretResponse, ClientListResponse
)
from src.schemas.common import ResponseBase
from src.services.client_service import ClientService
from src.core.dependencies import get_current_user
from src.models.user import User

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientWithSecretResponse)
async def create_client(
    client_input: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new client (user with client credentials).

    Returns client credentials (client_key and client_secret).
    The client_secret is only shown once, so save it securely.
    """
    client_service = ClientService(db)
    user, client_secret = await client_service.create_client(client_input)

    # Create response with secret and API key
    response_data = {
        "id": user.id,
        "name": user.username,
        "client_key": user.client_key,
        "client_secret": client_secret,  # Plain text, only shown once
        "api_key": user.api_key,  # For web UI access
        "email": user.email,
        "description": user.description,
        "contact_email": user.contact_email,
        "phone": user.phone,
        "webhook_url": user.webhook_url,
        "rate_limit": user.rate_limit,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_access_at": user.last_access_at
    }

    return ClientWithSecretResponse(**response_data)


@router.get("", response_model=ClientListResponse)
async def list_clients(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all clients (users)."""
    client_service = ClientService(db)
    result = await client_service.list_clients(None, limit, offset)

    # Convert User objects to ClientResponse
    items = []
    for user in result["items"]:
        items.append(ClientResponse(
            id=user.id,
            name=user.username,
            client_key=user.client_key,
            email=user.email,
            description=user.description,
            contact_email=user.contact_email,
            phone=user.phone,
            webhook_url=user.webhook_url,
            rate_limit=user.rate_limit,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_access_at=user.last_access_at
        ))

    return ClientListResponse(total=result["total"], items=items)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific client (user)."""
    client_service = ClientService(db)
    user = await client_service.get_client_by_id(client_id)

    if not user:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Client", client_id)

    return ClientResponse(
        id=user.id,
        name=user.username,
        client_key=user.client_key,
        email=user.email,
        description=user.description,
        contact_email=user.contact_email,
        phone=user.phone,
        webhook_url=user.webhook_url,
        rate_limit=user.rate_limit,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_access_at=user.last_access_at
    )


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a client (user)."""
    client_service = ClientService(db)
    user = await client_service.update_client(client_id, update_data)

    return ClientResponse(
        id=user.id,
        name=user.username,
        client_key=user.client_key,
        email=user.email,
        description=user.description,
        contact_email=user.contact_email,
        phone=user.phone,
        webhook_url=user.webhook_url,
        rate_limit=user.rate_limit,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_access_at=user.last_access_at
    )


@router.delete("/{client_id}", response_model=ResponseBase)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a client (user)."""
    client_service = ClientService(db)
    await client_service.delete_client(client_id)

    return ResponseBase(
        success=True,
        message=f"Client {client_id} deleted successfully"
    )


@router.post("/{client_id}/regenerate-credentials", response_model=ResponseBase)
async def regenerate_client_credentials(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate client credentials (client_key and client_secret).

    Returns new credentials. Save them securely as the secret cannot be retrieved later.
    """
    client_service = ClientService(db)
    new_key, new_secret = await client_service.regenerate_credentials(client_id)

    return ResponseBase(
        success=True,
        message="Credentials regenerated successfully",
        data={
            "client_key": new_key,
            "client_secret": new_secret
        }
    )

    Regenerate client credentials.

    The old credentials will be invalidated immediately.
    """
    client_service = ClientService(db)
    client_key, client_secret = await client_service.regenerate_credentials(
        client_id, current_user.id
    )

    return ResponseBase(
        success=True,
        message="Client credentials regenerated successfully",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "note": "Save these credentials securely. They won't be shown again."
        }
    )


@router.post("/{client_id}/activate", response_model=ClientResponse)
async def activate_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate a client."""
    client_service = ClientService(db)

    # Verify ownership
    client = await client_service.get_client_by_id(client_id)
    if not client or client.owner_id != current_user.id:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Client", client_id)

    client = await client_service.activate_client(client_id)
    return ClientResponse.model_validate(client)


@router.post("/{client_id}/deactivate", response_model=ClientResponse)
async def deactivate_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a client."""
    client_service = ClientService(db)

    # Verify ownership
    client = await client_service.get_client_by_id(client_id)
    if not client or client.owner_id != current_user.id:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Client", client_id)

    client = await client_service.deactivate_client(client_id)
    return ClientResponse.model_validate(client)
