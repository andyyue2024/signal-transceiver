"""
Analytics API endpoints.
Provides data analysis and trend visualization.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.core.dependencies import require_permissions
from src.services.analytics_service import DataAnalytics
from src.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/data/trends", response_model=ResponseBase)
async def get_data_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    current_user: User = Depends(require_permissions("data:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data trends and statistics over a period.

    Returns daily counts, breakdowns by type/symbol/strategy, and summary statistics.
    """
    analytics = DataAnalytics(db)
    result = await analytics.get_data_trends(
        days=days,
        strategy_id=strategy_id,
        data_type=data_type
    )

    return ResponseBase(
        success=True,
        message=f"Analytics for {days} days",
        data={
            "total_records": result.total_records,
            "period": {
                "start": result.period_start.isoformat(),
                "end": result.period_end.isoformat(),
                "days": days
            },
            "trends": [
                {"date": t.date.isoformat(), "count": t.count}
                for t in result.trends
            ],
            "by_type": result.by_type,
            "by_symbol": result.by_symbol,
            "by_strategy": result.by_strategy,
            "summary": result.summary
        }
    )


@router.get("/data/chart", response_model=ResponseBase)
async def get_data_chart(
    days: int = Query(30, ge=1, le=365),
    chart_type: str = Query("line", description="Chart type: line, bar, pie"),
    strategy_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("data:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get data formatted for charting libraries (Chart.js compatible).

    Requires permission: data:read
    """
    analytics = DataAnalytics(db)
    result = await analytics.get_data_trends(days=days, strategy_id=strategy_id)
    chart_data = analytics.format_for_chart(result, chart_type)

    return ResponseBase(
        success=True,
        message="Chart data generated",
        data=chart_data
    )


@router.get("/subscriptions", response_model=ResponseBase)
async def get_subscription_analytics(
    current_user: User = Depends(require_permissions("subscription:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription analytics.

    Requires permission: subscription:read
    """
    analytics = DataAnalytics(db)
    result = await analytics.get_subscription_analytics()

    return ResponseBase(
        success=True,
        message="Subscription analytics",
        data=result
    )


@router.get("/clients", response_model=ResponseBase)
async def get_client_analytics(
    current_user: User = Depends(require_permissions("admin:access")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get client analytics.

    Requires permission: admin:access
    """
    analytics = DataAnalytics(db)
    result = await analytics.get_user_analytics()

    return ResponseBase(
        success=True,
        message="Client analytics",
        data=result
    )


@router.get("/summary", response_model=ResponseBase)
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_permissions("data:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a comprehensive analytics summary.

    Requires permission: data:read
    """
    analytics = DataAnalytics(db)

    data_trends = await analytics.get_data_trends(days=days)
    subscription_stats = await analytics.get_subscription_analytics()
    user_stats = await analytics.get_user_analytics()

    return ResponseBase(
        success=True,
        message="Analytics summary",
        data={
            "period_days": days,
            "data": {
                "total": data_trends.total_records,
                "daily_average": data_trends.summary.get("average_daily", 0),
                "growth_rate": data_trends.summary.get("growth_rate_percent", 0),
                "unique_types": data_trends.summary.get("unique_types", 0),
                "unique_symbols": data_trends.summary.get("unique_symbols", 0)
            },
            "subscriptions": subscription_stats,
            "users": user_stats
        }
    )
