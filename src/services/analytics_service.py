"""
Data analytics service for trend analysis and reporting.
Provides data analysis functionality to help users understand data trends and patterns.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.data import Data
from src.models.subscription import Subscription
from src.models.user import User


@dataclass
class TrendPoint:
    """A single point in a trend."""
    date: date
    count: int
    value: Optional[float] = None


@dataclass
class AnalyticsResult:
    """Result of data analytics."""
    total_records: int
    period_start: date
    period_end: date
    trends: List[TrendPoint]
    by_type: Dict[str, int]
    by_symbol: Dict[str, int]
    by_strategy: Dict[str, int]
    summary: Dict[str, Any]


class DataAnalytics:
    """Service for analyzing data trends and patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_data_trends(
        self,
        days: int = 30,
        strategy_id: Optional[int] = None,
        client_id: Optional[int] = None,
        data_type: Optional[str] = None
    ) -> AnalyticsResult:
        """
        Analyze data trends over a period.

        Args:
            days: Number of days to analyze
            strategy_id: Filter by strategy
            client_id: Filter by client
            data_type: Filter by data type

        Returns:
            AnalyticsResult with trend data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Build query conditions
        conditions = [
            Data.execute_date >= start_date,
            Data.execute_date <= end_date
        ]

        if strategy_id:
            conditions.append(Data.strategy_id == strategy_id)
        if client_id:
            conditions.append(Data.client_id == client_id)
        if data_type:
            conditions.append(Data.type == data_type)

        # Get daily counts
        daily_query = (
            select(Data.execute_date, func.count(Data.id))
            .where(and_(*conditions))
            .group_by(Data.execute_date)
            .order_by(Data.execute_date)
        )
        daily_result = await self.db.execute(daily_query)
        daily_data = {row[0]: row[1] for row in daily_result.all()}

        # Fill in missing days
        trends = []
        current = start_date
        while current <= end_date:
            trends.append(TrendPoint(
                date=current,
                count=daily_data.get(current, 0)
            ))
            current += timedelta(days=1)

        # Get counts by type
        type_query = (
            select(Data.type, func.count(Data.id))
            .where(and_(*conditions))
            .group_by(Data.type)
        )
        type_result = await self.db.execute(type_query)
        by_type = {row[0]: row[1] for row in type_result.all()}

        # Get counts by symbol
        symbol_query = (
            select(Data.symbol, func.count(Data.id))
            .where(and_(*conditions))
            .group_by(Data.symbol)
            .order_by(func.count(Data.id).desc())
            .limit(20)
        )
        symbol_result = await self.db.execute(symbol_query)
        by_symbol = {row[0]: row[1] for row in symbol_result.all()}

        # Get counts by strategy
        strategy_query = (
            select(Data.strategy_id, func.count(Data.id))
            .where(and_(*conditions))
            .group_by(Data.strategy_id)
        )
        strategy_result = await self.db.execute(strategy_query)
        by_strategy = {str(row[0]): row[1] for row in strategy_result.all()}

        # Total count
        total_query = select(func.count(Data.id)).where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total_records = total_result.scalar() or 0

        # Calculate summary statistics
        total_in_period = sum(t.count for t in trends)
        avg_daily = total_in_period / days if days > 0 else 0
        max_daily = max(t.count for t in trends) if trends else 0
        min_daily = min(t.count for t in trends) if trends else 0

        # Calculate growth rate
        if len(trends) >= 2:
            first_week = sum(t.count for t in trends[:7])
            last_week = sum(t.count for t in trends[-7:])
            if first_week > 0:
                growth_rate = ((last_week - first_week) / first_week) * 100
            else:
                growth_rate = 100.0 if last_week > 0 else 0.0
        else:
            growth_rate = 0.0

        summary = {
            "total_in_period": total_in_period,
            "average_daily": round(avg_daily, 2),
            "max_daily": max_daily,
            "min_daily": min_daily,
            "growth_rate_percent": round(growth_rate, 2),
            "most_active_type": max(by_type, key=by_type.get) if by_type else None,
            "most_active_symbol": max(by_symbol, key=by_symbol.get) if by_symbol else None,
            "unique_types": len(by_type),
            "unique_symbols": len(by_symbol)
        }

        return AnalyticsResult(
            total_records=total_records,
            period_start=start_date,
            period_end=end_date,
            trends=trends,
            by_type=by_type,
            by_symbol=by_symbol,
            by_strategy=by_strategy,
            summary=summary
        )

    async def get_subscription_analytics(
        self,
        client_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get subscription analytics."""
        conditions = []
        if client_id:
            conditions.append(Subscription.client_id == client_id)

        # Total subscriptions
        total_query = select(func.count(Subscription.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Active subscriptions
        active_conditions = conditions + [Subscription.is_active == True]
        active_query = select(func.count(Subscription.id)).where(and_(*active_conditions))
        active_result = await self.db.execute(active_query)
        active = active_result.scalar() or 0

        # By type
        type_query = (
            select(Subscription.subscription_type, func.count(Subscription.id))
            .group_by(Subscription.subscription_type)
        )
        if conditions:
            type_query = type_query.where(and_(*conditions))
        type_result = await self.db.execute(type_query)
        by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_subscriptions": total,
            "active_subscriptions": active,
            "inactive_subscriptions": total - active,
            "by_type": by_type,
            "active_rate_percent": round((active / total * 100) if total > 0 else 0, 2)
        }

    async def get_client_analytics(self) -> Dict[str, Any]:
        """Get client analytics."""
        # Total clients
        total_result = await self.db.execute(select(func.count(Client.id)))
        total = total_result.scalar() or 0

        # Active clients
        active_result = await self.db.execute(
            select(func.count(Client.id)).where(Client.is_active == True)
        )
        active = active_result.scalar() or 0

        # Clients with data
        clients_with_data = await self.db.execute(
            select(func.count(func.distinct(Data.client_id)))
        )
        with_data = clients_with_data.scalar() or 0

        return {
            "total_clients": total,
            "active_clients": active,
            "inactive_clients": total - active,
            "clients_with_data": with_data,
            "active_rate_percent": round((active / total * 100) if total > 0 else 0, 2)
        }

    def format_for_chart(
        self,
        result: AnalyticsResult,
        chart_type: str = "line"
    ) -> Dict[str, Any]:
        """Format analytics result for charting libraries."""
        labels = [t.date.isoformat() for t in result.trends]
        values = [t.count for t in result.trends]

        if chart_type == "line":
            return {
                "type": "line",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Data Count",
                        "data": values,
                        "fill": False,
                        "borderColor": "rgb(75, 192, 192)"
                    }]
                }
            }
        elif chart_type == "bar":
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Data Count",
                        "data": values,
                        "backgroundColor": "rgba(54, 162, 235, 0.5)"
                    }]
                }
            }
        elif chart_type == "pie":
            return {
                "type": "pie",
                "data": {
                    "labels": list(result.by_type.keys()),
                    "datasets": [{
                        "data": list(result.by_type.values()),
                        "backgroundColor": [
                            "#FF6384", "#36A2EB", "#FFCE56",
                            "#4BC0C0", "#9966FF", "#FF9F40"
                        ]
                    }]
                }
            }

        return {"type": chart_type, "labels": labels, "values": values}
