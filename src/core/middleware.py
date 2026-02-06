"""
Middleware for logging, rate limiting, and request processing.
"""
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.core.exceptions import AppException


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Add request ID to request state
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration_ms}ms"
            )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- Error: {str(e)} - Duration: {duration_ms}ms"
            )
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling custom exceptions."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AppException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
        except Exception as e:
            logger.exception(f"Unhandled exception: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "details": {"error": str(e)} if logger.level("DEBUG") else {}
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app: FastAPI, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict = {}
        self.window_size = 60  # 1 minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        client_identifier = f"{client_ip}:{api_key[:8]}" if api_key else client_ip

        # Get current minute
        current_minute = int(time.time() / self.window_size)

        # Initialize or reset counter
        if client_identifier not in self.request_counts:
            self.request_counts[client_identifier] = {"minute": current_minute, "count": 0}

        if self.request_counts[client_identifier]["minute"] != current_minute:
            self.request_counts[client_identifier] = {"minute": current_minute, "count": 0}

        # Increment counter
        self.request_counts[client_identifier]["count"] += 1

        # Check limit
        if self.request_counts[client_identifier]["count"] > self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT",
                    "details": {"retry_after": self.window_size}
                },
                headers={"Retry-After": str(self.window_size)}
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - self.request_counts[client_identifier]["count"]
        )

        return response


def setup_middlewares(app: FastAPI):
    """Setup all middlewares for the application."""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
