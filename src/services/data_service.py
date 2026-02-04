"""
Data service for handling data upload and retrieval.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.data import Data
from src.models.strategy import Strategy
from src.models.user import User
from src.schemas.data import DataCreate, DataUpdate, DataFilter, DataBatchCreate
from src.core.exceptions import NotFoundError, ValidationError


class DataService:
    """Service for data operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_data(self, data_input: DataCreate, client_id: int) -> Data:
        """Create a new data record."""
        # Get strategy by strategy_id
        result = await self.db.execute(
            select(Strategy).where(Strategy.strategy_id == data_input.strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise NotFoundError("Strategy", data_input.strategy_id)

        # Create data record
        data = Data(
            type=data_input.type,
            symbol=data_input.symbol,
            execute_date=data_input.execute_date,
            description=data_input.description,
            payload=data_input.payload,
            metadata=data_input.metadata,
            source=data_input.source,
            strategy_id=strategy.id,
            client_id=client_id,
            status="pending"
        )

        self.db.add(data)
        await self.db.commit()
        await self.db.refresh(data)

        return data

    async def create_data_batch(
        self, batch: DataBatchCreate, client_id: int
    ) -> Dict[str, Any]:
        """Create multiple data records in batch."""
        success_count = 0
        error_count = 0
        errors = []

        for i, item in enumerate(batch.items):
            try:
                await self.create_data(item, client_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "index": i,
                    "error": str(e),
                    "data": item.model_dump()
                })

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    async def get_data_by_id(self, data_id: int) -> Optional[Data]:
        """Get data record by ID."""
        result = await self.db.execute(
            select(Data).where(Data.id == data_id)
        )
        return result.scalar_one_or_none()

    async def update_data(self, data_id: int, update_data: DataUpdate) -> Data:
        """Update a data record."""
        data = await self.get_data_by_id(data_id)
        if not data:
            raise NotFoundError("Data", data_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(data, key, value)

        data.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(data)

        return data

    async def delete_data(self, data_id: int) -> bool:
        """Delete a data record."""
        data = await self.get_data_by_id(data_id)
        if not data:
            raise NotFoundError("Data", data_id)

        await self.db.delete(data)
        await self.db.commit()

        return True

    async def list_data(
        self,
        filters: DataFilter,
        client_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """List data records with filters."""
        query = select(Data)
        conditions = []

        # Apply filters
        if client_id:
            conditions.append(Data.client_id == client_id)

        if filters.type:
            conditions.append(Data.type == filters.type)

        if filters.symbol:
            conditions.append(Data.symbol == filters.symbol)

        if filters.status:
            conditions.append(Data.status == filters.status)

        if filters.start_date:
            conditions.append(Data.execute_date >= filters.start_date)

        if filters.end_date:
            conditions.append(Data.execute_date <= filters.end_date)

        if filters.strategy_id:
            # Get strategy ID
            result = await self.db.execute(
                select(Strategy).where(Strategy.strategy_id == filters.strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if strategy:
                conditions.append(Data.strategy_id == strategy.id)

        if filters.cursor:
            conditions.append(Data.id > filters.cursor)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by created_at desc
        query = query.order_by(desc(Data.created_at))

        # Apply pagination
        if filters.cursor:
            query = query.limit(filters.limit + 1)
        else:
            query = query.offset(filters.offset).limit(filters.limit + 1)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Check if there are more items
        has_more = len(items) > filters.limit
        if has_more:
            items = items[:-1]

        next_cursor = items[-1].id if items and has_more else None

        # Get total count
        count_query = select(Data)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = len(list(count_result.scalars().all()))

        return {
            "total": total,
            "items": items,
            "has_more": has_more,
            "next_cursor": next_cursor
        }

    async def get_data_for_subscription(
        self,
        strategy_id: Optional[int] = None,
        last_data_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Data]:
        """Get new data for subscription."""
        query = select(Data)
        conditions = []

        if strategy_id:
            conditions.append(Data.strategy_id == strategy_id)

        if last_data_id:
            conditions.append(Data.id > last_data_id)

        if filters:
            if "type" in filters:
                conditions.append(Data.type == filters["type"])
            if "symbol" in filters:
                conditions.append(Data.symbol == filters["symbol"])

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Data.id).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
