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
from src.models.user import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse)
@router.post("/", response_model=SubscriptionResponse, include_in_schema=False)
async def create_subscription(
    subscription_input: SubscriptionCreate,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new subscription.

    Subscriptions allow clients to receive data updates via polling or WebSocket.
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.create_subscription(
        subscription_input, user.id
    )
    return SubscriptionResponse.model_validate(subscription)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """List all subscriptions for the authenticated client."""
    subscription_service = SubscriptionService(db)
    result = await subscription_service.list_subscriptions(user.id, limit, offset)

    return SubscriptionListResponse(
        total=result["total"],
        items=[SubscriptionResponse.model_validate(item) for item in result["items"]]
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific subscription."""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_subscription(subscription_id, user.id)

    if not subscription:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Subscription", subscription_id)

    return SubscriptionResponse.model_validate(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Update a subscription."""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.update_subscription(
        subscription_id, update_data, user.id
    )
    return SubscriptionResponse.model_validate(subscription)


@router.delete("/{subscription_id}", response_model=ResponseBase)
async def delete_subscription(
    subscription_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription."""
    subscription_service = SubscriptionService(db)
    await subscription_service.delete_subscription(subscription_id, user.id)

    return ResponseBase(
        success=True,
        message=f"Subscription {subscription_id} deleted successfully"
    )


@router.get("/{subscription_id}/data", response_model=SubscriptionDataResponse)
async def get_subscription_data(
    subscription_id: int,
    since: Optional[str] = Query(None, description="ISO 8601 timestamp"),
    limit: int = Query(100, ge=1, le=1000),
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data for a subscription (polling mode).

    Use the 'since' parameter to get only new data since a timestamp.
    """
    subscription_service = SubscriptionService(db)
    data = await subscription_service.get_subscription_data(
        subscription_id, user.id, since, limit
    )

    return SubscriptionDataResponse(
        subscription_id=subscription_id,
        data=data["items"],
        total=data["total"],
        has_more=data["has_more"]
    )


@router.get("/{subscription_id}/poll", response_model=SubscriptionDataResponse)
async def poll_subscription_data(
    subscription_id: int,
    since: Optional[str] = Query(None, description="ISO 8601 timestamp"),
    limit: int = Query(100, ge=1, le=1000),
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Poll for new data for a subscription.

    Alias for /{subscription_id}/data endpoint.
    Use the 'since' parameter to get only new data since a timestamp.
    """
    subscription_service = SubscriptionService(db)
    data = await subscription_service.get_subscription_data(
        subscription_id, user.id, since, limit
    )

    return SubscriptionDataResponse(
        subscription_id=subscription_id,
        data=data["items"],
        total=data["total"],
        has_more=data["has_more"]
    )


@router.post("/{subscription_id}/activate", response_model=ResponseBase)
async def activate_subscription(
    subscription_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Activate a subscription."""
    subscription_service = SubscriptionService(db)
    await subscription_service.activate_subscription(subscription_id, user.id)

    return ResponseBase(
        success=True,
        message=f"Subscription {subscription_id} activated"
    )


@router.post("/{subscription_id}/deactivate", response_model=ResponseBase)
async def deactivate_subscription(
    subscription_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a subscription."""
    subscription_service = SubscriptionService(db)
    await subscription_service.deactivate_subscription(subscription_id, user.id)

    return ResponseBase(
        success=True,
        message=f"Subscription {subscription_id} deactivated"
    )
