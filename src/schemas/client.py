"""
Pydantic schemas for Client model.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class ClientBase(BaseModel):
    """Base client schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    rate_limit: int = Field(default=100, ge=1, le=10000)


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    rate_limit: Optional[int] = Field(default=None, ge=1, le=10000)
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    """Client response schema."""
    id: int
    client_key: str
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_access_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientWithSecretResponse(ClientResponse):
    """Client response with secret (only shown once on creation)."""
    client_secret: str


class ClientListResponse(BaseModel):
    """Response schema for client list."""
    total: int
    items: List[ClientResponse]
