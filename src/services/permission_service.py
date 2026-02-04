"""
Permission service for managing roles and permissions.
"""
from datetime import datetime
from typing import Optional, List, Set
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.permission import Permission, Role, ClientPermission
from src.models.user import User
from src.core.exceptions import NotFoundError, ConflictError


class PermissionService:
    """Service for permission and role operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Permission operations
    async def create_permission(
        self, name: str, code: str, resource: str, action: str,
        description: str = None, category: str = "general"
    ) -> Permission:
        """Create a new permission."""
        # Check if code exists
        existing = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Permission with code '{code}' already exists")

        permission = Permission(
            name=name,
            code=code,
            resource=resource,
            action=action,
            description=description,
            category=category
        )

        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)

        return permission

    async def get_permission_by_code(self, code: str) -> Optional[Permission]:
        """Get permission by code."""
        result = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def list_permissions(self) -> List[Permission]:
        """List all permissions."""
        result = await self.db.execute(select(Permission))
        return list(result.scalars().all())

    # Role operations
    async def create_role(
        self, name: str, code: str, description: str = None,
        level: int = 0, permission_codes: List[str] = None
    ) -> Role:
        """Create a new role with permissions."""
        # Check if code exists
        existing = await self.db.execute(
            select(Role).where(Role.code == code)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role with code '{code}' already exists")

        role = Role(
            name=name,
            code=code,
            description=description,
            level=level
        )

        # Add permissions
        if permission_codes:
            for perm_code in permission_codes:
                perm = await self.get_permission_by_code(perm_code)
                if perm:
                    role.permissions.append(perm)

        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)

        return role

    async def get_role_by_code(self, code: str) -> Optional[Role]:
        """Get role by code."""
        result = await self.db.execute(
            select(Role).where(Role.code == code)
        )
        return result.scalar_one_or_none()

    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def list_roles(self) -> List[Role]:
        """List all roles."""
        result = await self.db.execute(select(Role))
        return list(result.scalars().all())

    async def add_permission_to_role(self, role_code: str, permission_code: str) -> Role:
        """Add permission to a role."""
        role = await self.get_role_by_code(role_code)
        if not role:
            raise NotFoundError("Role", role_code)

        permission = await self.get_permission_by_code(permission_code)
        if not permission:
            raise NotFoundError("Permission", permission_code)

        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)

        return role

    # Client permission operations
    async def assign_role_to_client(
        self, client_id: int, role_code: str
    ) -> ClientPermission:
        """Assign a role to a client."""
        role = await self.get_role_by_code(role_code)
        if not role:
            raise NotFoundError("Role", role_code)

        # Check if already assigned
        existing = await self.db.execute(
            select(ClientPermission).where(
                and_(
                    ClientPermission.client_id == client_id,
                    ClientPermission.role_id == role.id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role '{role_code}' already assigned to client")

        client_permission = ClientPermission(
            client_id=client_id,
            role_id=role.id,
            is_active=True
        )

        self.db.add(client_permission)
        await self.db.commit()
        await self.db.refresh(client_permission)

        return client_permission

    async def revoke_role_from_client(self, client_id: int, role_code: str) -> bool:
        """Revoke a role from a client."""
        role = await self.get_role_by_code(role_code)
        if not role:
            raise NotFoundError("Role", role_code)

        result = await self.db.execute(
            select(ClientPermission).where(
                and_(
                    ClientPermission.client_id == client_id,
                    ClientPermission.role_id == role.id
                )
            )
        )
        client_permission = result.scalar_one_or_none()

        if not client_permission:
            raise NotFoundError("ClientPermission")

        await self.db.delete(client_permission)
        await self.db.commit()

        return True

    async def get_client_permissions(self, client_id: int) -> Set[str]:
        """Get all permission codes for a client."""
        result = await self.db.execute(
            select(ClientPermission).where(
                and_(
                    ClientPermission.client_id == client_id,
                    ClientPermission.is_active == True
                )
            )
        )
        client_permissions = result.scalars().all()

        permission_codes = set()
        for cp in client_permissions:
            role = await self.get_role_by_id(cp.role_id)
            if role and role.permissions:
                for perm in role.permissions:
                    permission_codes.add(perm.code)

        return permission_codes

    async def check_client_permission(self, client_id: int, permission_code: str) -> bool:
        """Check if a client has a specific permission."""
        permissions = await self.get_client_permissions(client_id)
        return permission_code in permissions

    # Initialize default permissions and roles
    async def init_default_permissions(self):
        """Initialize default permissions."""
        default_permissions = [
            ("Read Data", "data:read", "data", "read", "Read data records"),
            ("Create Data", "data:create", "data", "create", "Create data records"),
            ("Update Data", "data:update", "data", "update", "Update data records"),
            ("Delete Data", "data:delete", "data", "delete", "Delete data records"),
            ("Read Subscription", "subscription:read", "subscription", "read", "Read subscriptions"),
            ("Create Subscription", "subscription:create", "subscription", "create", "Create subscriptions"),
            ("Update Subscription", "subscription:update", "subscription", "update", "Update subscriptions"),
            ("Delete Subscription", "subscription:delete", "subscription", "delete", "Delete subscriptions"),
            ("Read Strategy", "strategy:read", "strategy", "read", "Read strategies"),
            ("Create Strategy", "strategy:create", "strategy", "create", "Create strategies"),
            ("Admin Access", "admin:access", "admin", "all", "Full admin access"),
        ]

        for name, code, resource, action, description in default_permissions:
            try:
                await self.create_permission(name, code, resource, action, description)
            except ConflictError:
                pass  # Permission already exists

    async def init_default_roles(self):
        """Initialize default roles."""
        default_roles = [
            ("Reader", "reader", "Read-only access", 1, ["data:read", "subscription:read", "strategy:read"]),
            ("Writer", "writer", "Read and write access", 2, [
                "data:read", "data:create", "subscription:read", "subscription:create",
                "subscription:update", "strategy:read"
            ]),
            ("Admin", "admin", "Full admin access", 10, [
                "data:read", "data:create", "data:update", "data:delete",
                "subscription:read", "subscription:create", "subscription:update", "subscription:delete",
                "strategy:read", "strategy:create", "admin:access"
            ]),
        ]

        for name, code, description, level, permissions in default_roles:
            try:
                await self.create_role(name, code, description, level, permissions)
            except ConflictError:
                pass  # Role already exists
