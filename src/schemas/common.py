"""
Common response schemas.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel


class ResponseBase(BaseModel):
    """Base response schema."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    database: str = "connected"
