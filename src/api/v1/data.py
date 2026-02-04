"""
Data API endpoints for data upload and retrieval.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from src.config.database import get_db
from src.schemas.data import (
    DataCreate, DataUpdate, DataResponse, DataListResponse,
    DataFilter, DataBatchCreate, DataBatchResponse
)
from src.schemas.common import ResponseBase
from src.services.data_service import DataService
from src.core.dependencies import get_client_from_key
from src.models.user import User

router = APIRouter(prefix="/data", tags=["Data"])


@router.post("", response_model=DataResponse)
async def create_data(
    data_input: DataCreate,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new data record.

    Requires client authentication via X-Client-Key and X-Client-Secret headers.
    """
    data_service = DataService(db)
    data = await data_service.create_data(data_input, user.id)
    return DataResponse.model_validate(data)


@router.post("/batch", response_model=DataBatchResponse)
async def create_data_batch(
    batch: DataBatchCreate,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple data records in batch.

    Maximum 100 records per batch.
    """
    data_service = DataService(db)
    result = await data_service.create_data_batch(batch, user.id)
    return DataBatchResponse(**result)


@router.get("", response_model=DataListResponse)
async def list_data(
    type: Optional[str] = Query(None, description="Filter by data type"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    cursor: Optional[int] = Query(None, description="Cursor for pagination"),
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    List data records with filters.

    Supports both offset and cursor-based pagination.
    """
    filters = DataFilter(
        type=type,
        symbol=symbol,
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        limit=limit,
        offset=offset,
        cursor=cursor
    )

    data_service = DataService(db)
    result = await data_service.list_data(filters, user.id)

    return DataListResponse(
        total=result["total"],
        items=[DataResponse.model_validate(item) for item in result["items"]],
        has_more=result["has_more"],
        next_cursor=result["next_cursor"]
    )


@router.get("/{data_id}", response_model=DataResponse)
async def get_data(
    data_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific data record by ID."""
    data_service = DataService(db)
    data = await data_service.get_data_by_id(data_id)

    if not data:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Data", data_id)

    return DataResponse.model_validate(data)


@router.put("/{data_id}", response_model=DataResponse)
async def update_data(
    data_id: int,
    update_data: DataUpdate,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Update a data record."""
    data_service = DataService(db)
    data = await data_service.update_data(data_id, update_data)
    return DataResponse.model_validate(data)


@router.delete("/{data_id}", response_model=ResponseBase)
async def delete_data(
    data_id: int,
    user: User = Depends(get_client_from_key),
    db: AsyncSession = Depends(get_db)
):
    """Delete a data record."""
    data_service = DataService(db)
    await data_service.delete_data(data_id)

    return ResponseBase(
        success=True,
        message=f"Data record {data_id} deleted successfully"
    )
