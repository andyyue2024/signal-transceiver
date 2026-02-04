"""
Webhook service for third-party integrations.
Provides outbound webhook notifications for events.
"""
import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from loguru import logger


class WebhookEvent(str, Enum):
    """Webhook event types."""
    # Data events
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_BATCH_CREATED = "data.batch_created"

    # Subscription events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_DEACTIVATED = "subscription.deactivated"
    SUBSCRIPTION_DELETED = "subscription.deleted"

    # Client events
    CLIENT_CREATED = "client.created"
    CLIENT_ACTIVATED = "client.activated"
    CLIENT_DEACTIVATED = "client.deactivated"

    # System events
    SYSTEM_ALERT = "system.alert"
    SYSTEM_BACKUP_COMPLETED = "system.backup_completed"
    DAILY_REPORT = "system.daily_report"

    # Strategy events
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    id: str
    url: str
    secret: str
    events: List[WebhookEvent]
    enabled: bool = True
    client_id: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    timeout_seconds: int = 30


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    id: str
    webhook_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status: WebhookStatus
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


class WebhookService:
    """Service for managing and delivering webhooks."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._initialized = True

    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        secret: str,
        events: List[WebhookEvent],
        client_id: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookConfig:
        """Register a new webhook endpoint."""
        config = WebhookConfig(
            id=webhook_id,
            url=url,
            secret=secret,
            events=events,
            client_id=client_id,
            headers=headers or {}
        )
        self._webhooks[webhook_id] = config
        logger.info(f"Registered webhook: {webhook_id} -> {url}")
        return config

    def unregister_webhook(self, webhook_id: str):
        """Unregister a webhook endpoint."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")

    def enable_webhook(self, webhook_id: str):
        """Enable a webhook."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].enabled = True

    def disable_webhook(self, webhook_id: str):
        """Disable a webhook."""
        if webhook_id in self._webhooks:
            self._webhooks[webhook_id].enabled = False

    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Get webhook configuration."""
        return self._webhooks.get(webhook_id)

    def list_webhooks(self, client_id: Optional[int] = None) -> List[WebhookConfig]:
        """List all webhooks."""
        webhooks = list(self._webhooks.values())
        if client_id:
            webhooks = [w for w in webhooks if w.client_id == client_id]
        return webhooks

    async def trigger(
        self,
        event: WebhookEvent,
        payload: Dict[str, Any],
        client_id: Optional[int] = None
    ):
        """
        Trigger a webhook event.

        Args:
            event: The event type
            payload: Event payload data
            client_id: Optional client ID to filter webhooks
        """
        # Find matching webhooks
        for webhook in self._webhooks.values():
            if not webhook.enabled:
                continue

            if event not in webhook.events:
                continue

            if client_id and webhook.client_id and webhook.client_id != client_id:
                continue

            # Queue delivery
            delivery = WebhookDelivery(
                id=f"{webhook.id}_{int(time.time() * 1000)}",
                webhook_id=webhook.id,
                event=event,
                payload=payload,
                status=WebhookStatus.PENDING
            )

            await self._queue.put((webhook, delivery))
            logger.debug(f"Queued webhook delivery: {delivery.id}")

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for payload."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    async def _deliver(self, webhook: WebhookConfig, delivery: WebhookDelivery):
        """Deliver a webhook."""
        delivery.attempts += 1
        delivery.last_attempt = datetime.utcnow()
        delivery.status = WebhookStatus.RETRYING if delivery.attempts > 1 else WebhookStatus.PENDING

        # Prepare payload
        event_payload = {
            "id": delivery.id,
            "event": delivery.event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": delivery.payload
        }
        payload_json = json.dumps(event_payload, default=str)

        # Generate signature
        signature = self._generate_signature(payload_json, webhook.secret)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": delivery.event.value,
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": str(int(time.time())),
            "X-Webhook-Delivery-Id": delivery.id,
            **webhook.headers
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    data=payload_json,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=webhook.timeout_seconds)
                ) as response:
                    delivery.response_code = response.status
                    delivery.response_body = await response.text()

                    if 200 <= response.status < 300:
                        delivery.status = WebhookStatus.DELIVERED
                        logger.info(f"Webhook delivered: {delivery.id} -> {response.status}")
                    else:
                        delivery.status = WebhookStatus.FAILED
                        delivery.error = f"HTTP {response.status}"
                        logger.warning(f"Webhook failed: {delivery.id} -> {response.status}")

        except asyncio.TimeoutError:
            delivery.status = WebhookStatus.FAILED
            delivery.error = "Timeout"
            logger.error(f"Webhook timeout: {delivery.id}")

        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error = str(e)
            logger.error(f"Webhook error: {delivery.id} -> {e}")

        # Store delivery record
        self._deliveries.append(delivery)

        # Limit stored deliveries
        if len(self._deliveries) > 1000:
            self._deliveries = self._deliveries[-500:]

        # Retry if failed
        if delivery.status == WebhookStatus.FAILED and delivery.attempts < webhook.retry_count:
            await asyncio.sleep(2 ** delivery.attempts)  # Exponential backoff
            await self._queue.put((webhook, delivery))

    async def _worker(self):
        """Background worker to process webhook queue."""
        logger.info("Webhook worker started")

        while self._running:
            try:
                webhook, delivery = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                await self._deliver(webhook, delivery)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Webhook worker error: {e}")

        logger.info("Webhook worker stopped")

    def start(self):
        """Start the webhook worker."""
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._worker())

    def stop(self):
        """Stop the webhook worker."""
        self._running = False

    def get_deliveries(
        self,
        webhook_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Get delivery records."""
        deliveries = self._deliveries.copy()

        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        if status:
            deliveries = [d for d in deliveries if d.status == status]

        return deliveries[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        total = len(self._deliveries)
        delivered = sum(1 for d in self._deliveries if d.status == WebhookStatus.DELIVERED)
        failed = sum(1 for d in self._deliveries if d.status == WebhookStatus.FAILED)

        return {
            "registered_webhooks": len(self._webhooks),
            "active_webhooks": sum(1 for w in self._webhooks.values() if w.enabled),
            "total_deliveries": total,
            "delivered": delivered,
            "failed": failed,
            "success_rate": f"{(delivered / total * 100):.1f}%" if total > 0 else "N/A",
            "queue_size": self._queue.qsize(),
            "worker_running": self._running
        }


# Global webhook service instance
webhook_service = WebhookService()
