"""
Web API endpoints for monitoring and reporting.
"""
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import io

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user, get_admin_user
from src.models.user import User
from src.models.data import Data
from src.monitor.metrics import get_metrics, get_metrics_content_type
from src.monitor.performance import performance_monitor
from src.monitor.dashboard import system_dashboard
from src.monitor.alerts import alert_manager, AlertLevel
from src.report.generator import report_service

router = APIRouter(prefix="/monitor", tags=["Monitoring"])


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus format.
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@router.get("/dashboard", response_model=ResponseBase)
async def get_dashboard(
    current_user: User = Depends(get_current_user)
):
    """
    Get system dashboard data.

    Returns system health, performance metrics, and alerts.
    """
    data = system_dashboard.get_dashboard_data()

    return ResponseBase(
        success=True,
        message="Dashboard data retrieved",
        data=data
    )


@router.get("/performance", response_model=ResponseBase)
async def get_performance(
    minutes: int = Query(60, ge=1, le=1440),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance statistics.
    """
    stats = performance_monitor.get_current_stats()
    history = performance_monitor.get_history(minutes)
    warnings = performance_monitor.check_thresholds()

    return ResponseBase(
        success=True,
        message="Performance data retrieved",
        data={
            "current": stats,
            "history": history,
            "warnings": warnings
        }
    )


@router.get("/alerts", response_model=ResponseBase)
async def get_alerts(
    level: Optional[str] = Query(None, description="Filter by level"),
    active_only: bool = Query(True, description="Only show active alerts"),
    current_user: User = Depends(get_current_user)
):
    """
    Get system alerts.
    """
    if active_only:
        alerts = alert_manager.get_active_alerts()
    else:
        alerts = alert_manager._alerts

    if level:
        try:
            alert_level = AlertLevel(level)
            alerts = [a for a in alerts if a.level == alert_level]
        except ValueError:
            pass

    return ResponseBase(
        success=True,
        message="Alerts retrieved",
        data=[
            {
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "level": a.level.value,
                "source": a.source,
                "timestamp": a.timestamp.isoformat(),
                "resolved": a.resolved
            }
            for a in alerts
        ]
    )


@router.post("/alerts/{alert_id}/resolve", response_model=ResponseBase)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_admin_user)
):
    """
    Resolve an alert.
    """
    alert_manager.resolve(alert_id)

    return ResponseBase(
        success=True,
        message=f"Alert {alert_id} resolved"
    )


@router.post("/alerts/test", response_model=ResponseBase)
async def test_alert(
    title: str = Query(...),
    message: str = Query(...),
    level: str = Query("info"),
    current_user: User = Depends(get_admin_user)
):
    """
    Send a test alert.
    """
    try:
        alert_level = AlertLevel(level)
    except ValueError:
        alert_level = AlertLevel.INFO

    alert = await alert_manager.trigger(
        title=title,
        message=message,
        level=alert_level,
        source="test"
    )

    return ResponseBase(
        success=True,
        message="Test alert sent",
        data={"alert_id": alert.id}
    )


@router.get("/report/data")
async def download_data_report(
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    limit: int = Query(1000, ge=1, le=10000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download data report.
    """
    # Fetch data
    result = await db.execute(select(Data).limit(limit))
    records = result.scalars().all()

    data_dicts = [
        {
            "id": r.id,
            "type": r.type,
            "symbol": r.symbol,
            "execute_date": str(r.execute_date),
            "status": r.status,
            "created_at": str(r.created_at)
        }
        for r in records
    ]

    # Generate report
    content = await report_service.generate_data_report(
        data_dicts,
        format=format
    )

    # Return file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "pdf":
        filename = f"data_report_{timestamp}.pdf"
        media_type = "application/pdf"
    else:
        filename = f"data_report_{timestamp}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/report/performance")
async def download_performance_report(
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    minutes: int = Query(60, ge=1, le=1440),
    current_user: User = Depends(get_current_user)
):
    """
    Download performance report.
    """
    stats = performance_monitor.get_current_stats()
    history = performance_monitor.get_history(minutes)

    content = await report_service.generate_performance_report(
        stats,
        history,
        format=format
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format == "pdf":
        filename = f"performance_report_{timestamp}.pdf"
        media_type = "application/pdf"
    else:
        filename = f"performance_report_{timestamp}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/summary", response_model=ResponseBase)
async def get_summary_report(
    current_user: User = Depends(get_current_user)
):
    """
    Get summary report data.
    """
    summary = system_dashboard.get_summary_report()

    return ResponseBase(
        success=True,
        message="Summary report generated",
        data=summary
    )
