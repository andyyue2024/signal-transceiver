"""
Pydantic schemas for Subscription model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SubscriptionType(str, Enum):
    """Subscription type enumeration."""
    POLLING = "polling"
    WEBSOCKET = "websocket"


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    subscription_type: SubscriptionType = SubscriptionType.POLLING
    strategy_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    notification_enabled: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    notification_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    """Subscription response schema."""
    id: int
    client_id: int
    is_active: bool
    last_data_id: Optional[int] = None
    last_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Response schema for subscription list."""
    total: int
    items: List[SubscriptionResponse]


class SubscriptionDataResponse(BaseModel):
    """Response schema for subscription data fetch."""
    subscription_id: int
    data: List[Dict[str, Any]]
    last_id: Optional[int] = None
    has_more: bool = False
