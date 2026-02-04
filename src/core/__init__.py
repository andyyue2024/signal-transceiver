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
from src.core.scheduler import scheduler, setup_default_tasks, Scheduler
from src.core.cache import cache_manager, cached, CacheManager
from src.core.validation import data_validator, DataValidator
from src.core.compliance import target_compliance, TargetCompliance
from src.core.resource_access import ResourceAccessControl, ResourceAction
from src.core.health import health_checker, HealthChecker, HealthStatus
from src.core.rate_limiter import rate_limiter, RateLimiter, RateLimitConfig

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
    "setup_middlewares",
    # Scheduler
    "scheduler", "setup_default_tasks", "Scheduler",
    # Cache
    "cache_manager", "cached", "CacheManager",
    # Validation
    "data_validator", "DataValidator",
    # Compliance
    "target_compliance", "TargetCompliance",
    # Resource Access
    "ResourceAccessControl", "ResourceAction",
    # Health
    "health_checker", "HealthChecker", "HealthStatus",
    # Rate Limiter
    "rate_limiter", "RateLimiter", "RateLimitConfig"
]
