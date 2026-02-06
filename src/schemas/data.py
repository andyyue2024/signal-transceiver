"""
Pydantic schemas for Data model.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DataBase(BaseModel):
    """Base data schema."""
    type: str = Field(..., min_length=1, max_length=50)
    symbol: str = Field(..., min_length=1, max_length=50)
    execute_date: date
    description: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = Field(default=None, max_length=100)


class DataCreate(DataBase):
    """Schema for creating data record."""
    strategy_id: str = Field(..., min_length=1, max_length=50)


class DataUpdate(BaseModel):
    """Schema for updating data record."""
    description: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(default=None, max_length=20)


class DataResponse(DataBase):
    """Data response schema."""
    id: int
    strategy_id: int
    user_id: int
    status: str
    processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataListResponse(BaseModel):
    """Response schema for data list."""
    total: int
    items: List[DataResponse]
    has_more: bool = False
    next_cursor: Optional[int] = None


class DataFilter(BaseModel):
    """Filter parameters for data queries."""
    type: Optional[str] = None
    symbol: Optional[str] = None
    strategy_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    cursor: Optional[int] = None


class DataBatchCreate(BaseModel):
    """Schema for batch creating data records."""
    items: List[DataCreate] = Field(..., min_length=1, max_length=100)


class DataBatchResponse(BaseModel):
    """Response schema for batch data creation."""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = []
