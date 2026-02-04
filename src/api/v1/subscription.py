"""
Subscription API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.config.database import get_db
from src.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    SubscriptionListResponse, SubscriptionDataResponse
)
from src.schemas.common import ResponseBase
from src.services.subscription_service import SubscriptionService
from src.core.dependencies import get_client_from_key
from src.models.client import Client

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_input: SubscriptionCreate,
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new subscription.

    Subscriptions allow clients to receive data updates via polling or WebSocket.
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.create_subscription(
        subscription_input, client.id
    )
    return SubscriptionResponse.model_validate(subscription)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """List all subscriptions for the current client."""
    subscription_service = SubscriptionService(db)
    result = await subscription_service.list_subscriptions(client.id, limit, offset)

    return SubscriptionListResponse(
        total=result["total"],
        items=[SubscriptionResponse.model_validate(item) for item in result["items"]]
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific subscription."""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_subscription_by_id(subscription_id)

    if not subscription or subscription.client_id != client.id:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Subscription", subscription_id)

    return SubscriptionResponse.model_validate(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Update a subscription."""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.update_subscription(
        subscription_id, update_data, client.id
    )
    return SubscriptionResponse.model_validate(subscription)


@router.delete("/{subscription_id}", response_model=ResponseBase)
async def delete_subscription(
    subscription_id: int,
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription."""
    subscription_service = SubscriptionService(db)
    await subscription_service.delete_subscription(subscription_id, client.id)

    return ResponseBase(
        success=True,
        message=f"Subscription {subscription_id} deleted successfully"
    )


@router.get("/{subscription_id}/data", response_model=SubscriptionDataResponse)
async def get_subscription_data(
    subscription_id: int,
    limit: int = Query(50, ge=1, le=500),
    client: Client = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get new data for a subscription (polling endpoint).

    Returns data records that haven't been fetched yet.
    Updates the last_data_id to track what has been delivered.
    """
    subscription_service = SubscriptionService(db)
    result = await subscription_service.get_subscription_data(
        subscription_id, client.id, limit
    )

    return SubscriptionDataResponse(**result)
