"""
WebSocket endpoints for real-time data subscription.
"""
import asyncio
import json
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_maker
from src.core.security import hash_api_key
from src.services.subscription_service import SubscriptionService
from src.services.data_service import DataService
from loguru import logger

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        # client_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # WebSocket -> client_id
        self.connection_client_map: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, client_id: int):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)
        self.connection_client_map[websocket] = client_id

        logger.info(f"WebSocket connected: client_id={client_id}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        client_id = self.connection_client_map.get(websocket)
        if client_id:
            if client_id in self.active_connections:
                self.active_connections[client_id].discard(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
            del self.connection_client_map[websocket]
            logger.info(f"WebSocket disconnected: client_id={client_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast_to_client(self, message: dict, client_id: int):
        """Broadcast message to all connections of a client."""
        if client_id in self.active_connections:
            for websocket in self.active_connections[client_id]:
                await self.send_personal_message(message, websocket)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients."""
        for client_id in self.active_connections:
            await self.broadcast_to_client(message, client_id)


# Global connection manager
manager = ConnectionManager()


async def authenticate_client(client_key: str, client_secret: str) -> int:
    """Authenticate client and return client_id."""
    from src.models.client import Client
    from sqlalchemy import select

    async with async_session_maker() as db:
        result = await db.execute(
            select(Client).where(Client.client_key == client_key)
        )
        client = result.scalar_one_or_none()

        if not user:
            return None

        hashed_secret = hash_api_key(client_secret)
        if user.client_secret != hashed_secret:
            return None

        if not user.is_active:
            return None

        return user.id


@router.websocket("/ws/subscribe")
async def websocket_subscribe(
    websocket: WebSocket,
    client_key: str = Query(...),
    client_secret: str = Query(...)
):
    """
    WebSocket endpoint for real-time data subscription.

    Connect with client credentials as query parameters:
    ws://host/ws/subscribe?client_key=xxx&client_secret=xxx

    Messages:
    - Client -> Server: {"action": "subscribe", "subscription_id": 123}
    - Client -> Server: {"action": "unsubscribe", "subscription_id": 123}
    - Client -> Server: {"action": "ping"}
    - Server -> Client: {"type": "data", "subscription_id": 123, "data": [...]}
    - Server -> Client: {"type": "pong"}
    - Server -> Client: {"type": "error", "message": "..."}
    """
    # Authenticate client
    client_id = await authenticate_client(client_key, client_secret)
    if not client_id:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, client_id)

    # Track subscribed subscription IDs for this connection
    subscribed_ids: Set[int] = set()

    # Background task for polling subscriptions
    async def poll_subscriptions():
        while True:
            try:
                await asyncio.sleep(5)  # Poll every 5 seconds

                async with async_session_maker() as db:
                    subscription_service = SubscriptionService(db)

                    for sub_id in list(subscribed_ids):
                        try:
                            result = await subscription_service.get_subscription_data(
                                sub_id, client_id, limit=50
                            )

                            if result["data"]:
                                await manager.send_personal_message({
                                    "type": "data",
                                    "subscription_id": sub_id,
                                    "data": result["data"],
                                    "has_more": result["has_more"]
                                }, websocket)
                        except Exception as e:
                            logger.error(f"Error polling subscription {sub_id}: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in poll_subscriptions: {e}")

    # Start polling task
    poll_task = asyncio.create_task(poll_subscriptions())

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected successfully",
            "client_id": client_id
        })

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "subscribe":
                    subscription_id = message.get("subscription_id")
                    if subscription_id:
                        # Verify subscription belongs to client
                        async with async_session_maker() as db:
                            subscription_service = SubscriptionService(db)
                            sub = await subscription_service.get_subscription_by_id(subscription_id)

                            if sub and sub.client_id == client_id:
                                subscribed_ids.add(subscription_id)
                                await websocket.send_json({
                                    "type": "subscribed",
                                    "subscription_id": subscription_id
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"Subscription {subscription_id} not found"
                                })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "subscription_id is required"
                        })

                elif action == "unsubscribe":
                    subscription_id = message.get("subscription_id")
                    if subscription_id and subscription_id in subscribed_ids:
                        subscribed_ids.discard(subscription_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "subscription_id": subscription_id
                        })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })

    except WebSocketDisconnect:
        poll_task.cancel()
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        poll_task.cancel()
        manager.disconnect(websocket)


# Function to broadcast new data to subscribers
async def notify_new_data(strategy_id: int, data_id: int):
    """
    Notify all WebSocket subscribers about new data.

    This should be called when new data is created.
    """
    # This is a simplified version - in production, you might want to
    # use a message queue like Redis pub/sub for better scalability
    pass
