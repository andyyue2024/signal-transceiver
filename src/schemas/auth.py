"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(default=365, ge=1, le=3650)


class APIKeyResponse(BaseModel):
    """API key response schema."""
    api_key: str
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyVerify(BaseModel):
    """Schema for API key verification."""
    api_key: str = Field(..., min_length=32, max_length=64)


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
