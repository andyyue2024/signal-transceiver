"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.schemas.auth import LoginRequest, RegisterRequest, APIKeyCreate, APIKeyResponse
from src.schemas.user import UserResponse
from src.schemas.common import ResponseBase
from src.services.auth_service import AuthService
from src.core.dependencies import get_current_user
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ResponseBase)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Returns the user info and API key (shown only once).
    """
    from src.schemas.user import UserCreate

    auth_service = AuthService(db)
    user_data = UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone
    )

    user, api_key = await auth_service.register_user(user_data)

    return ResponseBase(
        success=True,
        message="User registered successfully",
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "api_key": api_key,
            "note": "Save this API key securely. It won't be shown again."
        }
    )


@router.post("/login", response_model=ResponseBase)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Returns user info on successful authentication.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(request.username, request.password)

    return ResponseBase(
        success=True,
        message="Login successful",
        data=UserResponse.model_validate(user).model_dump()
    )


@router.post("/regenerate-key", response_model=ResponseBase)
async def regenerate_api_key(
    request: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate API key for the current user.

    The old key will be invalidated immediately.
    """
    auth_service = AuthService(db)
    new_api_key = await auth_service.regenerate_api_key(
        current_user.id,
        request.expires_in_days
    )

    return ResponseBase(
        success=True,
        message="API key regenerated successfully",
        data={
            "api_key": new_api_key,
            "note": "Save this API key securely. It won't be shown again."
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password", response_model=ResponseBase)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    auth_service = AuthService(db)
    await auth_service.update_password(current_user.id, old_password, new_password)

    return ResponseBase(
        success=True,
        message="Password changed successfully"
    )
