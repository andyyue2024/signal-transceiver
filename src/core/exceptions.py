"""
Custom exceptions for the application.
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(AppException):
    """Authorization/permission denied."""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            details=details
        )


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: Optional[Any] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class ConflictError(AppException):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details
        )


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            status_code=429,
            details={"retry_after": retry_after}
        )


class DatabaseError(AppException):
    """Database operation error."""

    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DB_ERROR",
            status_code=500,
            details=details
        )
