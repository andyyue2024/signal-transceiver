"""
Admin API endpoints for system management.
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timedelta, timezone

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.core.dependencies import get_admin_user
from src.core.scheduler import scheduler, setup_default_tasks
from src.core.cache import cache_manager
from src.services.backup_service import backup_service
from src.services.audit_service import AuditLogger, AuditAction
from src.models.user import User
from src.models.log import Log
from src.models.data import Data
from src.config.settings import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=ResponseBase)
async def get_system_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system statistics."""
    # User count
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0

    # Client count (users with client_key are clients)
    client_count = (await db.execute(
        select(func.count(User.id)).where(User.client_key.isnot(None))
    )).scalar() or 0
    active_clients = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0

    # Data count
    data_count = (await db.execute(select(func.count(Data.id)))).scalar() or 0

    # Today's data
    today = datetime.now(timezone.utc).date()
    today_data = (await db.execute(
        select(func.count(Data.id)).where(Data.execute_date == today)
    )).scalar() or 0

    # Log count
    log_count = (await db.execute(select(func.count(Log.id)))).scalar() or 0

    # Cache stats
    cache_stats = cache_manager.get_all_stats()

    # Scheduler status
    scheduler_status = scheduler.get_status()

    return ResponseBase(
        success=True,
        message="System statistics retrieved",
        data={
            "users": {"total": user_count},
            "clients": {"total": client_count, "active": active_clients},
            "data": {"total": data_count, "today": today_data},
            "logs": {"total": log_count},
            "cache": cache_stats,
            "scheduler": {
                "running": scheduler_status["running"],
                "tasks": scheduler_status["task_count"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@router.get("/logs", response_model=ResponseBase)
async def get_logs(
    log_type: Optional[str] = Query(None, description="Filter by log type"),
    level: Optional[str] = Query(None, description="Filter by level"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system logs."""
    query = select(Log)

    if log_type:
        query = query.where(Log.log_type == log_type)
    if level:
        query = query.where(Log.level == level)
    if user_id:
        query = query.where(Log.user_id == user_id)

    query = query.order_by(Log.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return ResponseBase(
        success=True,
        message=f"Retrieved {len(logs)} logs",
        data=[
            {
                "id": log.id,
                "log_type": log.log_type,
                "action": log.action,
                "level": log.level,
                "message": log.message,
                "user_id": log.user_id,
                "client_id": log.client_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    )


@router.get("/audit-trail", response_model=ResponseBase)
async def get_audit_trail(
    resource: Optional[str] = Query(None),
    resource_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    audit_logger = AuditLogger(db)

    if user_id:
        logs = await audit_logger.get_user_activity(user_id, limit)
    elif resource and resource_id:
        logs = await audit_logger.get_audit_trail(resource, resource_id, limit)
    else:
        result = await db.execute(
            select(Log)
            .where(Log.log_type == "audit")
            .where(Log.created_at >= cutoff)
            .order_by(Log.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

    return ResponseBase(
        success=True,
        message=f"Retrieved {len(logs)} audit records",
        data=[
            {
                "id": log.id,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "user_id": log.user_id,
                "client_id": log.client_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    )


@router.post("/scheduler/start", response_model=ResponseBase)
async def start_scheduler(
    admin: User = Depends(get_admin_user)
):
    """Start the task scheduler."""
    setup_default_tasks()
    scheduler.start()

    return ResponseBase(
        success=True,
        message="Scheduler started",
        data=scheduler.get_status()
    )


@router.post("/scheduler/stop", response_model=ResponseBase)
async def stop_scheduler(
    admin: User = Depends(get_admin_user)
):
    """Stop the task scheduler."""
    scheduler.stop()

    return ResponseBase(
        success=True,
        message="Scheduler stopped"
    )


@router.get("/scheduler/status", response_model=ResponseBase)
async def get_scheduler_status(
    admin: User = Depends(get_admin_user)
):
    """Get scheduler status."""
    return ResponseBase(
        success=True,
        message="Scheduler status retrieved",
        data=scheduler.get_status()
    )


@router.post("/scheduler/tasks/{task_id}/enable", response_model=ResponseBase)
async def enable_task(
    task_id: str,
    admin: User = Depends(get_admin_user)
):
    """Enable a scheduled task."""
    scheduler.enable_task(task_id)

    return ResponseBase(
        success=True,
        message=f"Task {task_id} enabled"
    )


@router.post("/scheduler/tasks/{task_id}/disable", response_model=ResponseBase)
async def disable_task(
    task_id: str,
    admin: User = Depends(get_admin_user)
):
    """Disable a scheduled task."""
    scheduler.disable_task(task_id)

    return ResponseBase(
        success=True,
        message=f"Task {task_id} disabled"
    )


@router.get("/cache/stats", response_model=ResponseBase)
async def get_cache_stats(
    admin: User = Depends(get_admin_user)
):
    """Get cache statistics."""
    return ResponseBase(
        success=True,
        message="Cache statistics retrieved",
        data=cache_manager.get_all_stats()
    )


@router.post("/cache/clear", response_model=ResponseBase)
async def clear_cache(
    cache_name: Optional[str] = Query(None, description="Specific cache to clear"),
    admin: User = Depends(get_admin_user)
):
    """Clear cache."""
    if cache_name:
        cache = cache_manager.get_cache(cache_name)
        await cache.clear()
        message = f"Cache '{cache_name}' cleared"
    else:
        await cache_manager.clear_all()
        message = "All caches cleared"

    return ResponseBase(
        success=True,
        message=message
    )


@router.get("/backups", response_model=ResponseBase)
async def list_backups(
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user)
):
    """List available backups."""
    backups = await backup_service.list_backups(limit=limit)

    return ResponseBase(
        success=True,
        message=f"Found {len(backups)} backups",
        data={
            "backups": [b.to_dict() for b in backups],
            "stats": backup_service.get_stats()
        }
    )


@router.post("/backups/create", response_model=ResponseBase)
async def create_backup(
    background_tasks: BackgroundTasks,
    compress: bool = Query(True),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a database backup."""
    # Log the action
    audit_logger = AuditLogger(db)
    await audit_logger.log(
        action=AuditAction.BACKUP_CREATE,
        user_id=admin.id,
        resource="database"
    )

    # Get database path from settings
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    try:
        backup_info = await backup_service.create_backup(db_path, compress=compress)

        return ResponseBase(
            success=True,
            message="Backup created successfully",
            data=backup_info.to_dict()
        )
    except FileNotFoundError as e:
        return ResponseBase(
            success=False,
            message=str(e)
        )


@router.post("/backups/{filename}/restore", response_model=ResponseBase)
async def restore_backup(
    filename: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Restore a database backup."""
    # Log the action
    audit_logger = AuditLogger(db)
    await audit_logger.log(
        action=AuditAction.SYSTEM_CONFIG_CHANGE,
        user_id=admin.id,
        resource="database",
        details={"action": "restore", "backup": filename}
    )

    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    try:
        await backup_service.restore_backup(filename, db_path, overwrite=True)

        return ResponseBase(
            success=True,
            message=f"Database restored from {filename}"
        )
    except FileNotFoundError as e:
        return ResponseBase(
            success=False,
            message=str(e)
        )


@router.delete("/backups/{filename}", response_model=ResponseBase)
async def delete_backup(
    filename: str,
    admin: User = Depends(get_admin_user)
):
    """Delete a backup."""
    deleted = await backup_service.delete_backup(filename)

    if deleted:
        return ResponseBase(
            success=True,
            message=f"Backup {filename} deleted"
        )
    else:
        return ResponseBase(
            success=False,
            message="Backup not found"
        )


@router.get("/config", response_model=ResponseBase)
async def get_config(
    admin: User = Depends(get_admin_user)
):
    """Get current configuration (non-sensitive)."""
    return ResponseBase(
        success=True,
        message="Configuration retrieved",
        data={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "database_type": "sqlite" if "sqlite" in settings.database_url else "other",
            "cors_origins": settings.cors_origins,
            "api_key_expiry_days": settings.api_key_expiry_days
        }
    )
