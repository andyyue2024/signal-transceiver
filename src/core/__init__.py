"""Core package - security, dependencies, exceptions, middleware."""
from src.core.security import (
    generate_api_key, hash_api_key, generate_client_credentials,
    verify_password, get_password_hash, generate_token,
    calculate_expiry, is_expired
)
from src.core.exceptions import (
    AppException, AuthenticationError, AuthorizationError,
    NotFoundError, ValidationError, ConflictError,
    RateLimitError, DatabaseError
)
from src.core.dependencies import (
    get_current_user, get_current_active_user, get_admin_user,
    get_client_from_key, require_permissions
)
from src.core.middleware import setup_middlewares

__all__ = [
    # Security
    "generate_api_key", "hash_api_key", "generate_client_credentials",
    "verify_password", "get_password_hash", "generate_token",
    "calculate_expiry", "is_expired",
    # Exceptions
    "AppException", "AuthenticationError", "AuthorizationError",
    "NotFoundError", "ValidationError", "ConflictError",
    "RateLimitError", "DatabaseError",
    # Dependencies
    "get_current_user", "get_current_active_user", "get_admin_user",
    "get_client_from_key", "require_permissions",
    # Middleware
    "setup_middlewares"
]
