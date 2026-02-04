"""
Admin API endpoints for system management.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.config.database import get_db
from src.schemas.common import ResponseBase
from src.services.permission_service import PermissionService
from src.core.dependencies import get_admin_user
from src.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/init-permissions", response_model=ResponseBase)
async def init_permissions(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize default permissions and roles.

    This should be called once during initial system setup.
    """
    permission_service = PermissionService(db)
    await permission_service.init_default_permissions()
    await permission_service.init_default_roles()

    return ResponseBase(
        success=True,
        message="Default permissions and roles initialized"
    )


@router.get("/permissions", response_model=ResponseBase)
async def list_permissions(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all permissions."""
    permission_service = PermissionService(db)
    permissions = await permission_service.list_permissions()

    return ResponseBase(
        success=True,
        message="Permissions retrieved",
        data=[{
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "resource": p.resource,
            "action": p.action,
            "category": p.category
        } for p in permissions]
    )


@router.get("/roles", response_model=ResponseBase)
async def list_roles(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all roles with their permissions."""
    permission_service = PermissionService(db)
    roles = await permission_service.list_roles()

    return ResponseBase(
        success=True,
        message="Roles retrieved",
        data=[{
            "id": r.id,
            "name": r.name,
            "code": r.code,
            "level": r.level,
            "permissions": [p.code for p in r.permissions]
        } for r in roles]
    )


@router.post("/clients/{client_id}/roles/{role_code}", response_model=ResponseBase)
async def assign_role_to_client(
    client_id: int,
    role_code: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a client."""
    permission_service = PermissionService(db)
    await permission_service.assign_role_to_client(client_id, role_code)

    return ResponseBase(
        success=True,
        message=f"Role '{role_code}' assigned to client {client_id}"
    )


@router.delete("/clients/{client_id}/roles/{role_code}", response_model=ResponseBase)
async def revoke_role_from_client(
    client_id: int,
    role_code: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a role from a client."""
    permission_service = PermissionService(db)
    await permission_service.revoke_role_from_client(client_id, role_code)

    return ResponseBase(
        success=True,
        message=f"Role '{role_code}' revoked from client {client_id}"
    )


@router.get("/clients/{client_id}/permissions", response_model=ResponseBase)
async def get_client_permissions(
    client_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all permissions for a client."""
    permission_service = PermissionService(db)
    permissions = await permission_service.get_client_permissions(client_id)

    return ResponseBase(
        success=True,
        message="Client permissions retrieved",
        data=list(permissions)
    )
