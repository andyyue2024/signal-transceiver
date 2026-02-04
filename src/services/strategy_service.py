"""
Strategy service for managing strategies.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.strategy import Strategy
from src.schemas.strategy import StrategyCreate, StrategyUpdate
from src.core.exceptions import NotFoundError, ConflictError


class StrategyService:
    """Service for strategy operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_strategy(self, strategy_input: StrategyCreate) -> Strategy:
        """Create a new strategy."""
        # Check if strategy_id exists
        existing = await self.db.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_input.strategy_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Strategy with id '{strategy_input.strategy_id}' already exists")

        strategy = Strategy(
            strategy_id=strategy_input.strategy_id,
            name=strategy_input.name,
            description=strategy_input.description,
            type=strategy_input.type,
            category=strategy_input.category,
            config=strategy_input.config,
            parameters=strategy_input.parameters,
            priority=strategy_input.priority,
            version=strategy_input.version,
            is_active=True
        )

        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)

        return strategy

    async def get_strategy_by_id(self, id: int) -> Optional[Strategy]:
        """Get strategy by database ID."""
        result = await self.db.execute(
            select(Strategy).where(Strategy.id == id)
        )
        return result.scalar_one_or_none()

    async def get_strategy_by_strategy_id(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by strategy_id."""
        result = await self.db.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        return result.scalar_one_or_none()

    async def update_strategy(
        self, strategy_id: str, update_data: StrategyUpdate
    ) -> Strategy:
        """Update a strategy."""
        strategy = await self.get_strategy_by_strategy_id(strategy_id)

        if not strategy:
            raise NotFoundError("Strategy", strategy_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(strategy, key, value)

        strategy.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(strategy)

        return strategy

    async def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a strategy."""
        strategy = await self.get_strategy_by_strategy_id(strategy_id)

        if not strategy:
            raise NotFoundError("Strategy", strategy_id)

        await self.db.delete(strategy)
        await self.db.commit()

        return True

    async def list_strategies(
        self,
        limit: int = 50,
        offset: int = 0,
        type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List strategies with optional filters."""
        query = select(Strategy)

        if type:
            query = query.where(Strategy.type == type)
        if category:
            query = query.where(Strategy.category == category)
        if is_active is not None:
            query = query.where(Strategy.is_active == is_active)

        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Get total count
        count_query = select(Strategy)
        if type:
            count_query = count_query.where(Strategy.type == type)
        if category:
            count_query = count_query.where(Strategy.category == category)
        if is_active is not None:
            count_query = count_query.where(Strategy.is_active == is_active)

        count_result = await self.db.execute(count_query)
        total = len(list(count_result.scalars().all()))

        return {
            "total": total,
            "items": items
        }
