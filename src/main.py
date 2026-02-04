"""
Signal Transceiver - Main Application Entry Point

A subscription service for data collection and distribution.
Provides RESTful APIs and WebSocket for real-time data streaming.
"""
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.config.database import init_db
from src.api import api_router, ws_router
from src.web.api import router as monitor_router
from src.web.admin_ui import router as admin_ui_router
from src.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from src.core.exceptions import AppException
from src.core.scheduler import scheduler, setup_default_tasks
from src.utils.logger import setup_logging, logger
from src.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start scheduler with default tasks
    setup_default_tasks()
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    scheduler.stop()
    logger.info("Scheduler stopped")
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Signal Transceiver API

A subscription service for data collection and distribution.

### Features:
- **Data Upload**: Clients can upload data records via REST API
- **Subscriptions**: Subscribe to data streams via polling or WebSocket
- **Authentication**: API Key based authentication
- **Authorization**: Role-based access control

### Authentication:
- User API: Use `X-API-Key` header with your user API key
- Client API: Use `X-Client-Key` and `X-Client-Secret` headers

### WebSocket:
Connect to `/ws/subscribe?client_key=xxx&client_secret=xxx` for real-time updates.
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add custom middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)


# Exception handler for AppException
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
app.include_router(monitor_router, prefix="/api/v1")
app.include_router(admin_ui_router)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database="connected"
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
