"""
Pydantic schemas for Client (now User-based).
Client and User are now unified - these schemas provide backward compatibility.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class ClientBase(BaseModel):
    """Base client schema - maps to User model fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Username")
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=20, alias="phone")
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    rate_limit: int = Field(default=100, ge=1, le=10000)


class ClientCreate(BaseModel):
    """Schema for creating a client (user)."""
    name: str = Field(..., min_length=1, max_length=100, description="Username")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, max_length=100, description="User password")
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    rate_limit: int = Field(default=100, ge=1, le=10000)


class ClientUpdate(BaseModel):
    """Schema for updating a client (user)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    rate_limit: Optional[int] = Field(default=None, ge=1, le=10000)
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    """Client response schema - maps to User model."""
    id: int
    name: str  # username
    client_key: str
    email: str
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    rate_limit: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_access_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientWithSecretResponse(ClientResponse):
    """Client response with secret (only shown once on creation)."""
    client_secret: str
    api_key: str  # Also return the API key for web UI access


class ClientListResponse(BaseModel):
    """Response schema for client list."""
    total: int
    items: List[ClientResponse]
