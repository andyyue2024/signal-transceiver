"""
Audit logging service for tracking all user operations.
Records detailed audit trails for compliance and security.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.log import Log


class AuditAction(str, Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    API_KEY_REGENERATE = "api_key_regenerate"
    PASSWORD_CHANGE = "password_change"

    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # Client management
    CLIENT_CREATE = "client_create"
    CLIENT_UPDATE = "client_update"
    CLIENT_DELETE = "client_delete"
    CLIENT_ACTIVATE = "client_activate"
    CLIENT_DEACTIVATE = "client_deactivate"

    # Data operations
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_BATCH_CREATE = "data_batch_create"
    DATA_QUERY = "data_query"

    # Subscription operations
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_DELETE = "subscription_delete"
    SUBSCRIPTION_DATA_FETCH = "subscription_data_fetch"

    # Strategy operations
    STRATEGY_CREATE = "strategy_create"
    STRATEGY_UPDATE = "strategy_update"
    STRATEGY_DELETE = "strategy_delete"

    # Permission operations
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    PERMISSION_CREATE = "permission_create"

    # System operations
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    REPORT_GENERATE = "report_generate"
    BACKUP_CREATE = "backup_create"


class AuditLogger:
    """Service for recording audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        level: str = "info"
    ) -> Log:
        """Record an audit log entry."""
        log_entry = Log(
            log_type="audit",
            action=action.value,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            status_code=status_code,
            response_time_ms=response_time_ms,
            level=level,
            message=f"{action.value}: {resource or 'system'}{'#' + str(resource_id) if resource_id else ''}"
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        logger.debug(f"Audit log: {action.value} by user={user_id}")

        return log_entry

    async def log_access(
        self,
        method: str,
        path: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: int = 0
    ) -> Log:
        """Record an access log entry."""
        log_entry = Log(
            log_type="access",
            action="api_request",
            method=method,
            path=path,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            response_time_ms=response_time_ms,
            level="info" if status_code < 400 else "error",
            message=f"{method} {path} - {status_code}"
        )

        self.db.add(log_entry)
        await self.db.commit()

        return log_entry

    async def log_error(
        self,
        error_type: str,
        message: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None
    ) -> Log:
        """Record an error log entry."""
        log_entry = Log(
            log_type="error",
            action="error",
            resource=error_type,
            user_id=user_id,
            path=path,
            details=details or {},
            level="error",
            message=message
        )

        self.db.add(log_entry)
        await self.db.commit()

        return log_entry

    async def log_security(
        self,
        event: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: str = "warning"
    ) -> Log:
        """Record a security log entry."""
        log_entry = Log(
            log_type="security",
            action=event,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {},
            level=level,
            message=f"Security event: {event}"
        )

        self.db.add(log_entry)
        await self.db.commit()

        return log_entry

    async def get_user_activity(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Log]:
        """Get activity logs for a specific user."""
        result = await self.db.execute(
            select(Log)
            .where(Log.user_id == user_id)
            .order_by(desc(Log.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_client_activity(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Log]:
        """Get activity logs for a specific client (user)."""
        result = await self.db.execute(
            select(Log)
            .where(Log.user_id == user_id)
            .order_by(desc(Log.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_security_events(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Log]:
        """Get security event logs."""
        conditions = [Log.log_type == "security"]

        if start_date:
            conditions.append(Log.created_at >= start_date)
        if end_date:
            conditions.append(Log.created_at <= end_date)

        result = await self.db.execute(
            select(Log)
            .where(and_(*conditions))
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_audit_trail(
        self,
        resource: str,
        resource_id: int,
        limit: int = 50
    ) -> List[Log]:
        """Get audit trail for a specific resource."""
        result = await self.db.execute(
            select(Log)
            .where(
                and_(
                    Log.log_type == "audit",
                    Log.resource == resource,
                    Log.resource_id == resource_id
                )
            )
            .order_by(desc(Log.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_logs_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get summary of logs for the specified period."""
        from sqlalchemy import func
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        # Count by type
        type_counts = {}
        for log_type in ["access", "audit", "error", "security"]:
            result = await self.db.execute(
                select(func.count(Log.id))
                .where(
                    and_(
                        Log.log_type == log_type,
                        Log.created_at >= cutoff
                    )
                )
            )
            type_counts[log_type] = result.scalar() or 0

        # Error count
        error_result = await self.db.execute(
            select(func.count(Log.id))
            .where(
                and_(
                    Log.level == "error",
                    Log.created_at >= cutoff
                )
            )
        )
        error_count = error_result.scalar() or 0

        return {
            "period_days": days,
            "total_logs": sum(type_counts.values()),
            "by_type": type_counts,
            "error_count": error_count,
            "generated_at": datetime.utcnow().isoformat()
        }
