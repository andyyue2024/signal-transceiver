"""
Webhook API endpoints.
Provides webhook management for third-party integrations.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel, HttpUrl

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user, get_admin_user
from src.services.webhook_service import webhook_service, WebhookEvent, WebhookStatus
from src.models.user import User

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookCreate(BaseModel):
    """Request to create a webhook."""
    url: str
    events: List[str]
    secret: Optional[str] = None
    headers: Optional[dict] = None


class WebhookUpdate(BaseModel):
    """Request to update a webhook."""
    url: Optional[str] = None
    events: Optional[List[str]] = None
    enabled: Optional[bool] = None


@router.post("", response_model=ResponseBase)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Register a new webhook endpoint.

    Events:
    - data.created, data.updated, data.deleted, data.batch_created
    - subscription.created, subscription.activated, subscription.deactivated
    - client.created, client.activated, client.deactivated
    - system.alert, system.backup_completed, system.daily_report
    - strategy.created, strategy.updated
    """
    import secrets

    # Generate webhook ID and secret
    webhook_id = f"wh_{secrets.token_hex(8)}"
    secret = data.secret or secrets.token_hex(32)

    # Validate events
    valid_events = []
    for event_str in data.events:
        try:
            valid_events.append(WebhookEvent(event_str))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event_str}"
            )

    webhook = webhook_service.register_webhook(
        webhook_id=webhook_id,
        url=data.url,
        secret=secret,
        events=valid_events,
        headers=data.headers
    )

    return ResponseBase(
        success=True,
        message="Webhook registered",
        data={
            "id": webhook.id,
            "url": webhook.url,
            "secret": secret,  # Only shown on creation
            "events": [e.value for e in webhook.events],
            "enabled": webhook.enabled
        }
    )


@router.get("", response_model=ResponseBase)
async def list_webhooks(
    current_user: User = Depends(get_current_user)
):
    """List all registered webhooks."""
    webhooks = webhook_service.list_webhooks()

    return ResponseBase(
        success=True,
        message=f"Found {len(webhooks)} webhooks",
        data={
            "webhooks": [
                {
                    "id": w.id,
                    "url": w.url,
                    "events": [e.value for e in w.events],
                    "enabled": w.enabled
                }
                for w in webhooks
            ]
        }
    )


@router.get("/{webhook_id}", response_model=ResponseBase)
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get webhook details."""
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return ResponseBase(
        success=True,
        message="Webhook found",
        data={
            "id": webhook.id,
            "url": webhook.url,
            "events": [e.value for e in webhook.events],
            "enabled": webhook.enabled,
            "retry_count": webhook.retry_count,
            "timeout_seconds": webhook.timeout_seconds
        }
    )


@router.patch("/{webhook_id}", response_model=ResponseBase)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a webhook."""
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if data.url:
        webhook.url = data.url

    if data.events:
        webhook.events = [WebhookEvent(e) for e in data.events]

    if data.enabled is not None:
        webhook.enabled = data.enabled

    return ResponseBase(
        success=True,
        message="Webhook updated",
        data={
            "id": webhook.id,
            "url": webhook.url,
            "events": [e.value for e in webhook.events],
            "enabled": webhook.enabled
        }
    )


@router.delete("/{webhook_id}", response_model=ResponseBase)
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook."""
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    webhook_service.unregister_webhook(webhook_id)

    return ResponseBase(
        success=True,
        message="Webhook deleted"
    )


@router.post("/{webhook_id}/enable", response_model=ResponseBase)
async def enable_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Enable a webhook."""
    webhook_service.enable_webhook(webhook_id)

    return ResponseBase(
        success=True,
        message="Webhook enabled"
    )


@router.post("/{webhook_id}/disable", response_model=ResponseBase)
async def disable_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Disable a webhook."""
    webhook_service.disable_webhook(webhook_id)

    return ResponseBase(
        success=True,
        message="Webhook disabled"
    )


@router.get("/{webhook_id}/deliveries", response_model=ResponseBase)
async def get_webhook_deliveries(
    webhook_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Get delivery history for a webhook."""
    status_filter = WebhookStatus(status) if status else None
    deliveries = webhook_service.get_deliveries(
        webhook_id=webhook_id,
        status=status_filter,
        limit=limit
    )

    return ResponseBase(
        success=True,
        message=f"Found {len(deliveries)} deliveries",
        data={
            "deliveries": [
                {
                    "id": d.id,
                    "event": d.event.value,
                    "status": d.status.value,
                    "attempts": d.attempts,
                    "last_attempt": d.last_attempt.isoformat() if d.last_attempt else None,
                    "response_code": d.response_code,
                    "error": d.error
                }
                for d in deliveries
            ]
        }
    )


@router.post("/{webhook_id}/test", response_model=ResponseBase)
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Send a test event to a webhook."""
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Trigger test event
    await webhook_service.trigger(
        event=WebhookEvent.SYSTEM_ALERT,
        payload={
            "type": "test",
            "message": "This is a test webhook delivery",
            "triggered_by": current_user.username
        }
    )

    return ResponseBase(
        success=True,
        message="Test event queued for delivery"
    )


@router.get("/stats", response_model=ResponseBase)
async def get_webhook_stats(
    admin: User = Depends(get_admin_user)
):
    """Get webhook statistics (admin only)."""
    return ResponseBase(
        success=True,
        message="Webhook statistics",
        data=webhook_service.get_stats()
    )


@router.get("/events", response_model=ResponseBase)
async def list_webhook_events(
    current_user: User = Depends(get_current_user)
):
    """List all available webhook events."""
    events = [
        {"value": e.value, "name": e.name}
        for e in WebhookEvent
    ]

    return ResponseBase(
        success=True,
        message="Available webhook events",
        data={"events": events}
    )
