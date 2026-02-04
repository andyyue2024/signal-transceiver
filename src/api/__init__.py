"""API package."""
from fastapi import APIRouter

from src.api.v1 import router as v1_router
from src.api.websocket import router as ws_router

# Create main API router
api_router = APIRouter()

# Include v1 API
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router", "ws_router"]
