"""
Fine-grained permission control based on Strategy ID and data type.
Implements resource-level access control.
"""
from datetime import datetime
from typing import Optional, List, Set, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.core.exceptions import AuthorizationError


class ResourceAction(str, Enum):
    """Actions that can be performed on resources."""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ResourcePermission:
    """Permission for a specific resource."""
    resource_type: str  # 'strategy', 'data_type', 'symbol'
    resource_id: str    # The specific ID or '*' for all
    actions: Set[ResourceAction] = field(default_factory=set)
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientResourceAccess:
    """Resource access configuration for a client."""
    client_id: int
    permissions: List[ResourcePermission] = field(default_factory=list)
    deny_list: List[str] = field(default_factory=list)  # Explicitly denied resources


class ResourceAccessControl:
    """Fine-grained resource access control."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._access_cache: Dict[int, ClientResourceAccess] = {}

    async def check_access(
        self,
        client_id: int,
        resource_type: str,
        resource_id: str,
        action: ResourceAction
    ) -> bool:
        """
        Check if a client has access to a specific resource.

        Args:
            client_id: The client ID
            resource_type: Type of resource ('strategy', 'data_type', 'symbol')
            resource_id: The specific resource ID
            action: The action to perform

        Returns:
            True if access is allowed, False otherwise
        """
        access = await self._get_client_access(client_id)

        if not access:
            return False

        # Check deny list first
        deny_key = f"{resource_type}:{resource_id}"
        if deny_key in access.deny_list or f"{resource_type}:*" in access.deny_list:
            return False

        # Check permissions
        for perm in access.permissions:
            if self._permission_matches(perm, resource_type, resource_id, action):
                return True

        return False

    def _permission_matches(
        self,
        perm: ResourcePermission,
        resource_type: str,
        resource_id: str,
        action: ResourceAction
    ) -> bool:
        """Check if a permission matches the requested access."""
        # Check resource type
        if perm.resource_type != resource_type and perm.resource_type != "*":
            return False

        # Check resource ID (supports wildcards)
        if perm.resource_id != resource_id and perm.resource_id != "*":
            # Check prefix matching (e.g., "strategy_*" matches "strategy_001")
            if not perm.resource_id.endswith("*"):
                return False
            prefix = perm.resource_id[:-1]
            if not resource_id.startswith(prefix):
                return False

        # Check action
        if action not in perm.actions and ResourceAction("*") not in perm.actions:
            return False

        return True

    async def _get_client_access(self, client_id: int) -> Optional[ClientResourceAccess]:
        """Get or load client access configuration."""
        if client_id in self._access_cache:
            return self._access_cache[client_id]

        # Load from database
        access = await self._load_client_access(client_id)
        if access:
            self._access_cache[client_id] = access

        return access

    async def _load_client_access(self, client_id: int) -> Optional[ClientResourceAccess]:
        """Load client (user) access configuration from database."""
        from src.models.permission import ClientPermission, Role
        from src.models.user import User

        # Get user (client)
        result = await self.db.execute(
            select(User).where(User.id == client_id)
        )
        client = result.scalar_one_or_none()

        if not client or not client.is_active:
            return None

        # Get client's roles and permissions
        result = await self.db.execute(
            select(ClientPermission)
            .where(
                and_(
                    ClientPermission.client_id == client_id,
                    ClientPermission.is_active == True
                )
            )
        )
        client_permissions = result.scalars().all()

        # Build access configuration
        permissions = []

        for cp in client_permissions:
            role = await self.db.get(Role, cp.role_id)
            if role and role.permissions:
                for perm in role.permissions:
                    # Convert permission to resource permission
                    rp = ResourcePermission(
                        resource_type=perm.resource,
                        resource_id="*",  # Default to all
                        actions={ResourceAction(perm.action) if perm.action != "all" else ResourceAction.READ}
                    )
                    if perm.action == "all":
                        rp.actions = {ResourceAction.READ, ResourceAction.CREATE, ResourceAction.UPDATE, ResourceAction.DELETE}
                    permissions.append(rp)

        return ClientResourceAccess(
            client_id=client_id,
            permissions=permissions
        )

    def clear_cache(self, client_id: Optional[int] = None):
        """Clear access cache."""
        if client_id:
            self._access_cache.pop(client_id, None)
        else:
            self._access_cache.clear()

    async def grant_resource_access(
        self,
        client_id: int,
        resource_type: str,
        resource_id: str,
        actions: List[ResourceAction]
    ):
        """Grant access to a specific resource."""
        # This would typically update database records
        # For now, we'll update the cache
        access = await self._get_client_access(client_id)
        if not access:
            access = ClientResourceAccess(client_id=client_id)
            self._access_cache[client_id] = access

        access.permissions.append(ResourcePermission(
            resource_type=resource_type,
            resource_id=resource_id,
            actions=set(actions)
        ))

        logger.info(f"Granted {actions} access to {resource_type}:{resource_id} for client {client_id}")

    async def revoke_resource_access(
        self,
        client_id: int,
        resource_type: str,
        resource_id: str
    ):
        """Revoke access to a specific resource."""
        access = await self._get_client_access(client_id)
        if access:
            access.permissions = [
                p for p in access.permissions
                if not (p.resource_type == resource_type and p.resource_id == resource_id)
            ]
            logger.info(f"Revoked access to {resource_type}:{resource_id} for client {client_id}")


def require_resource_access(
    resource_type: str,
    action: ResourceAction = ResourceAction.READ
):
    """
    Decorator for requiring resource-level access.

    Usage:
        @require_resource_access("strategy", ResourceAction.READ)
        async def get_strategy_data(strategy_id: str, client: Client):
            ...
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract client and resource_id from arguments
            client = kwargs.get("client")
            resource_id = kwargs.get("strategy_id") or kwargs.get("resource_id")
            db = kwargs.get("db")

            if not client or not resource_id or not db:
                raise AuthorizationError("Missing required parameters for access check")

            rac = ResourceAccessControl(db)
            has_access = await rac.check_access(
                client_id=client.id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action
            )

            if not has_access:
                raise AuthorizationError(
                    f"Access denied to {resource_type}:{resource_id}",
                    details={"resource_type": resource_type, "resource_id": resource_id, "action": action.value}
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
