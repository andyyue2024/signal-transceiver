"""
Pydantic schemas for Strategy model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    """Base strategy schema."""
    strategy_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: str = Field(default="default", max_length=50)
    category: Optional[str] = Field(default=None, max_length=50)
    config: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: int = Field(default=0, ge=0, le=100)
    version: str = Field(default="1.0.0", max_length=20)


class StrategyCreate(StrategyBase):
    """Schema for creating a strategy."""
    pass


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    type: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=50)
    config: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    version: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Strategy response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """Response schema for strategy list."""
    total: int
    items: List[StrategyResponse]
