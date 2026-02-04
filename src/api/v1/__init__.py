"""API v1 package - RESTful API endpoints."""
from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.data import router as data_router
from src.api.v1.subscription import router as subscription_router
from src.api.v1.client import router as client_router
from src.api.v1.strategy import router as strategy_router
from src.api.v1.admin import router as admin_router

# Create main v1 router
router = APIRouter()

# Include all routers
router.include_router(auth_router)
router.include_router(data_router)
router.include_router(subscription_router)
router.include_router(client_router)
router.include_router(strategy_router)
router.include_router(admin_router)

__all__ = ["router"]
