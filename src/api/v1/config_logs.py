"""
Configuration and Log management API endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from src.schemas.common import ResponseBase
from src.core.dependencies import get_current_user, get_admin_user
from src.core.config_manager import config_manager, ConfigType
from src.services.log_search_service import log_search_service, LogLevel, LogSearchQuery
from src.models.user import User

config_router = APIRouter(prefix="/config", tags=["Configuration"])
logs_router = APIRouter(prefix="/logs", tags=["Logs"])


# Configuration API
class ConfigUpdate(BaseModel):
    """Request to update config."""
    value: str
    type: str = "string"
    description: Optional[str] = None
    is_secret: bool = False


@config_router.get("", response_model=ResponseBase)
async def list_configs(
    prefix: Optional[str] = Query(None, description="Filter by prefix"),
    admin: User = Depends(get_admin_user)
):
    """List all configurations (admin only)."""
    configs = config_manager.list_all(prefix)

    return ResponseBase(
        success=True,
        message=f"Found {len(configs)} configurations",
        data={
            "configs": [c.to_dict() for c in configs]
        }
    )


@config_router.get("/{key:path}", response_model=ResponseBase)
async def get_config(
    key: str,
    admin: User = Depends(get_admin_user)
):
    """Get a configuration value."""
    value = config_manager.get(key)

    if value is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    configs = [c for c in config_manager.list_all() if c.key == key]

    return ResponseBase(
        success=True,
        message="Configuration found",
        data=configs[0].to_dict() if configs else {"key": key, "value": value}
    )


@config_router.put("/{key:path}", response_model=ResponseBase)
async def update_config(
    key: str,
    data: ConfigUpdate,
    admin: User = Depends(get_admin_user)
):
    """Update a configuration value (admin only)."""
    try:
        config_type = ConfigType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid type: {data.type}")

    config = config_manager.set(
        key=key,
        value=data.value,
        config_type=config_type,
        description=data.description or "",
        is_secret=data.is_secret,
        updated_by=admin.id
    )

    return ResponseBase(
        success=True,
        message="Configuration updated",
        data=config.to_dict()
    )


@config_router.delete("/{key:path}", response_model=ResponseBase)
async def delete_config(
    key: str,
    admin: User = Depends(get_admin_user)
):
    """Delete a configuration (admin only)."""
    if config_manager.delete(key):
        return ResponseBase(success=True, message="Configuration deleted")
    raise HTTPException(status_code=404, detail="Configuration not found")


@config_router.get("/export/all", response_model=ResponseBase)
async def export_configs(
    admin: User = Depends(get_admin_user)
):
    """Export all configurations."""
    return ResponseBase(
        success=True,
        message="Configurations exported",
        data=config_manager.export()
    )


# Logs API
@logs_router.get("", response_model=ResponseBase)
async def search_logs(
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_admin_user)
):
    """Search system logs (admin only)."""
    level_filter = LogLevel(level.upper()) if level else None

    from datetime import timedelta
    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = LogSearchQuery(
        level=level_filter,
        source=source,
        keyword=keyword,
        user_id=user_id,
        start_time=start_time,
        limit=limit,
        offset=offset
    )

    logs = log_search_service.search(query)

    return ResponseBase(
        success=True,
        message=f"Found {len(logs)} logs",
        data={
            "logs": [l.to_dict() for l in logs],
            "query": {
                "level": level,
                "source": source,
                "keyword": keyword,
                "hours": hours
            }
        }
    )


@logs_router.get("/stats", response_model=ResponseBase)
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168),
    admin: User = Depends(get_admin_user)
):
    """Get log statistics."""
    stats = log_search_service.get_stats(hours)

    return ResponseBase(
        success=True,
        message="Log statistics",
        data=stats
    )


@logs_router.get("/{log_id}", response_model=ResponseBase)
async def get_log(
    log_id: str,
    admin: User = Depends(get_admin_user)
):
    """Get a specific log entry."""
    log = log_search_service.get_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    return ResponseBase(
        success=True,
        message="Log found",
        data=log.to_dict()
    )


@logs_router.post("/cleanup", response_model=ResponseBase)
async def cleanup_logs(
    days: int = Query(7, ge=1, le=90),
    admin: User = Depends(get_admin_user)
):
    """Cleanup old logs (admin only)."""
    removed = log_search_service.cleanup(days)

    return ResponseBase(
        success=True,
        message=f"Removed {removed} old log entries",
        data={"removed": removed, "retention_days": days}
    )


@logs_router.get("/levels", response_model=ResponseBase)
async def get_log_levels():
    """Get available log levels."""
    return ResponseBase(
        success=True,
        message="Log levels",
        data={"levels": [l.value for l in LogLevel]}
    )
