"""
Client management API endpoints.
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
    Create a new client application.

    Returns client credentials (client_key and client_secret).
    The client_secret is only shown once, so save it securely.
    """
    client_service = ClientService(db)
    client, client_secret = await client_service.create_client(
        client_input, current_user.id
    )

    # Create response with secret
    response_data = ClientWithSecretResponse.model_validate(client)
    response_data.client_secret = client_secret

    return response_data


@router.get("", response_model=ClientListResponse)
async def list_clients(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all clients owned by the current user."""
    client_service = ClientService(db)
    result = await client_service.list_clients(current_user.id, limit, offset)

    return ClientListResponse(
        total=result["total"],
        items=[ClientResponse.model_validate(item) for item in result["items"]]
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific client."""
    client_service = ClientService(db)
    client = await client_service.get_client_by_id(client_id)

    if not client or client.owner_id != current_user.id:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Client", client_id)

    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a client."""
    client_service = ClientService(db)
    client = await client_service.update_client(
        client_id, update_data, current_user.id
    )
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}", response_model=ResponseBase)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a client."""
    client_service = ClientService(db)
    await client_service.delete_client(client_id, current_user.id)

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
