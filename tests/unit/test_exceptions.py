"""
Tests for exception classes and middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.exceptions import (
    AppException, AuthenticationError, AuthorizationError,
    NotFoundError, ValidationError, ConflictError,
    RateLimitError, DatabaseError
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_app_exception_defaults(self):
        """Test AppException with defaults."""
        exc = AppException(message="Test error")

        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.error_code == "APP_ERROR"

    def test_app_exception_custom(self):
        """Test AppException with custom values."""
        exc = AppException(
            message="Custom error",
            status_code=400,
            error_code="CUSTOM_ERROR",
            details={"field": "value"}
        )

        assert exc.message == "Custom error"
        assert exc.status_code == 400
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == {"field": "value"}

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError(message="Invalid credentials")

        assert exc.status_code == 401
        assert exc.error_code == "AUTH_ERROR"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError(message="Access denied")

        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"

    def test_not_found_error(self):
        """Test NotFoundError."""
        exc = NotFoundError(resource="User", resource_id=123)

        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert "User" in exc.message

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError(message="Invalid data")

        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"

    def test_conflict_error(self):
        """Test ConflictError."""
        exc = ConflictError(message="Conflict")

        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError(message="Too many requests")

        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT"

    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError(message="Database error")

        assert exc.status_code == 500
        assert exc.error_code == "DB_ERROR"

    def test_exception_str(self):
        """Test exception string representation."""
        exc = AppException(message="Test")

        assert str(exc) == "Test"

    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"field": "email", "error": "invalid format"}
        exc = ValidationError(message="Validation failed", details=details)

        assert exc.details == details


class TestExceptionInheritance:
    """Test exception inheritance."""

    def test_all_inherit_from_app_exception(self):
        """Test all exceptions inherit from AppException."""
        exceptions = [
            (AuthenticationError, {"message": "test"}),
            (AuthorizationError, {"message": "test"}),
            (NotFoundError, {"resource": "Test"}),
            (ValidationError, {"message": "test"}),
            (ConflictError, {"message": "test"}),
            (RateLimitError, {"message": "test"}),
            (DatabaseError, {"message": "test"})
        ]

        for exc_class, kwargs in exceptions:
            exc = exc_class(**kwargs)
            assert isinstance(exc, AppException)
            assert isinstance(exc, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
