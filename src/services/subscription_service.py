"""
Subscription service for managing subscriptions and data delivery.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription
from src.models.strategy import Strategy
from src.models.data import Data
from src.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from src.core.exceptions import NotFoundError, ValidationError


class SubscriptionService:
    """Service for subscription operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(
        self, subscription_input: SubscriptionCreate, client_id: int
    ) -> Subscription:
        """Create a new subscription."""
        strategy_id = None

        # Get strategy if provided
        if subscription_input.strategy_id:
            result = await self.db.execute(
                select(Strategy).where(Strategy.strategy_id == subscription_input.strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                raise NotFoundError("Strategy", subscription_input.strategy_id)
            strategy_id = strategy.id

        # Create subscription
        subscription = Subscription(
            name=subscription_input.name,
            description=subscription_input.description,
            subscription_type=subscription_input.subscription_type.value,
            client_id=client_id,
            strategy_id=strategy_id,
            filters=subscription_input.filters,
            webhook_url=subscription_input.webhook_url,
            notification_enabled=subscription_input.notification_enabled,
            is_active=True
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def update_subscription(
        self, subscription_id: int, update_data: SubscriptionUpdate, client_id: int
    ) -> Subscription:
        """Update a subscription."""
        subscription = await self.get_subscription_by_id(subscription_id)

        if not subscription:
            raise NotFoundError("Subscription", subscription_id)

        if subscription.client_id != client_id:
            raise ValidationError("You can only update your own subscriptions")

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(subscription, key, value)

        subscription.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def delete_subscription(self, subscription_id: int, client_id: int) -> bool:
        """Delete a subscription."""
        subscription = await self.get_subscription_by_id(subscription_id)

        if not subscription:
            raise NotFoundError("Subscription", subscription_id)

        if subscription.client_id != client_id:
            raise ValidationError("You can only delete your own subscriptions")

        await self.db.delete(subscription)
        await self.db.commit()

        return True

    async def list_subscriptions(
        self, client_id: int, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """List subscriptions for a client."""
        query = select(Subscription).where(Subscription.client_id == client_id)
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Get total count
        count_result = await self.db.execute(
            select(Subscription).where(Subscription.client_id == client_id)
        )
        total = len(list(count_result.scalars().all()))

        return {
            "total": total,
            "items": items
        }

    async def get_subscription_data(
        self, subscription_id: int, client_id: int, limit: int = 50
    ) -> Dict[str, Any]:
        """Get new data for a subscription (polling)."""
        subscription = await self.get_subscription_by_id(subscription_id)

        if not subscription:
            raise NotFoundError("Subscription", subscription_id)

        if subscription.client_id != client_id:
            raise ValidationError("You can only access your own subscriptions")

        # Build query for new data
        query = select(Data)
        conditions = []

        if subscription.strategy_id:
            conditions.append(Data.strategy_id == subscription.strategy_id)

        if subscription.last_data_id:
            conditions.append(Data.id > subscription.last_data_id)

        # Apply subscription filters
        if subscription.filters:
            if "type" in subscription.filters:
                conditions.append(Data.type == subscription.filters["type"])
            if "symbol" in subscription.filters:
                conditions.append(Data.symbol == subscription.filters["symbol"])

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Data.id).limit(limit + 1)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        has_more = len(items) > limit
        if has_more:
            items = items[:-1]

        # Update last_data_id
        if items:
            subscription.last_data_id = items[-1].id
            subscription.last_notified_at = datetime.utcnow()
            await self.db.commit()

        return {
            "subscription_id": subscription_id,
            "data": [self._data_to_dict(item) for item in items],
            "last_id": items[-1].id if items else subscription.last_data_id,
            "has_more": has_more
        }

    async def get_active_websocket_subscriptions(self, client_id: int) -> List[Subscription]:
        """Get active WebSocket subscriptions for a client."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.client_id == client_id,
                    Subscription.subscription_type == "websocket",
                    Subscription.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    def _data_to_dict(self, data: Data) -> Dict[str, Any]:
        """Convert Data model to dictionary."""
        return {
            "id": data.id,
            "type": data.type,
            "symbol": data.symbol,
            "execute_date": data.execute_date.isoformat() if data.execute_date else None,
            "description": data.description,
            "payload": data.payload,
            "metadata": data.metadata,
            "strategy_id": data.strategy_id,
            "status": data.status,
            "created_at": data.created_at.isoformat() if data.created_at else None
        }
