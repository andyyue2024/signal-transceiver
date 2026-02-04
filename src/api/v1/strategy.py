"""
Strategy API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.config.database import get_db
from src.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyResponse, StrategyListResponse
)
from src.schemas.common import ResponseBase
from src.services.strategy_service import StrategyService
from src.core.dependencies import get_current_user, get_admin_user
from src.models.user import User

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.post("", response_model=StrategyResponse)
async def create_strategy(
    strategy_input: StrategyCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new strategy.

    Requires admin privileges.
    """
    strategy_service = StrategyService(db)
    strategy = await strategy_service.create_strategy(strategy_input)
    return StrategyResponse.model_validate(strategy)


@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    type: Optional[str] = Query(None, description="Filter by strategy type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all strategies."""
    strategy_service = StrategyService(db)
    result = await strategy_service.list_strategies(
        limit=limit,
        offset=offset,
        type=type,
        category=category,
        is_active=is_active
    )

    return StrategyListResponse(
        total=result["total"],
        items=[StrategyResponse.model_validate(item) for item in result["items"]]
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific strategy by strategy_id."""
    strategy_service = StrategyService(db)
    strategy = await strategy_service.get_strategy_by_strategy_id(strategy_id)

    if not strategy:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Strategy", strategy_id)

    return StrategyResponse.model_validate(strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    update_data: StrategyUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a strategy.

    Requires admin privileges.
    """
    strategy_service = StrategyService(db)
    strategy = await strategy_service.update_strategy(strategy_id, update_data)
    return StrategyResponse.model_validate(strategy)


@router.delete("/{strategy_id}", response_model=ResponseBase)
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a strategy.

    Requires admin privileges.
    """
    strategy_service = StrategyService(db)
    await strategy_service.delete_strategy(strategy_id)

    return ResponseBase(
        success=True,
        message=f"Strategy '{strategy_id}' deleted successfully"
    )
