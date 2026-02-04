"""
Notification and Export API endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from typing import Optional, List
from pydantic import BaseModel

from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user
from src.services.notification_service import (
    notification_service, NotificationType, NotificationPriority
)
from src.services.export_service import data_export_service, ExportFormat
from src.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationCreate(BaseModel):
    """Request to create a notification."""
    title: str
    message: str
    type: str = "info"
    priority: str = "normal"


@router.get("", response_model=ResponseBase)
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """List notifications for the current user."""
    notifications = notification_service.list_for_user(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )

    return ResponseBase(
        success=True,
        message=f"Found {len(notifications)} notifications",
        data={
            "notifications": [n.to_dict() for n in notifications],
            "unread_count": notification_service.get_unread_count(current_user.id)
        }
    )


@router.get("/unread-count", response_model=ResponseBase)
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications."""
    count = notification_service.get_unread_count(current_user.id)

    return ResponseBase(
        success=True,
        message="Unread count",
        data={"count": count}
    )


@router.post("/{notification_id}/read", response_model=ResponseBase)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    notification = notification_service.mark_as_read(notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return ResponseBase(
        success=True,
        message="Notification marked as read"
    )


@router.post("/read-all", response_model=ResponseBase)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    count = notification_service.mark_all_as_read(current_user.id)

    return ResponseBase(
        success=True,
        message=f"Marked {count} notifications as read",
        data={"count": count}
    )


@router.delete("/{notification_id}", response_model=ResponseBase)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    success = notification_service.delete(notification_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return ResponseBase(
        success=True,
        message="Notification deleted"
    )


# Export endpoints
export_router = APIRouter(prefix="/export", tags=["Export"])


@export_router.post("/data", response_class=Response)
async def export_data(
    format: str = Query("csv", description="Export format: csv, json, jsonl"),
    strategy_id: Optional[int] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    current_user: User = Depends(get_current_user)
):
    """
    Export data in the specified format.

    Returns a downloadable file.
    """
    from src.config.database import get_db
    from src.models.data import Data
    from sqlalchemy import select

    # This is a simplified example - in production, use proper DB session
    # For now, return sample data structure
    sample_data = [
        {
            "id": 1,
            "type": "signal",
            "symbol": "AAPL",
            "strategy_id": "strategy_001",
            "execute_date": "2024-02-01",
            "description": "Sample data"
        }
    ]

    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")

    result = data_export_service.export(
        data=sample_data,
        format=export_format,
        filename_prefix="data_export"
    )

    content_types = {
        ExportFormat.JSON: "application/json",
        ExportFormat.CSV: "text/csv",
        ExportFormat.JSONL: "application/x-ndjson"
    }

    return Response(
        content=result.content,
        media_type=content_types[export_format],
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )


@export_router.get("/formats", response_model=ResponseBase)
async def get_export_formats():
    """Get available export formats."""
    return ResponseBase(
        success=True,
        message="Available export formats",
        data={
            "formats": [f.value for f in ExportFormat],
            "descriptions": {
                "json": "JSON format with metadata",
                "csv": "CSV spreadsheet format",
                "jsonl": "JSON Lines format (one record per line)"
            }
        }
    )
