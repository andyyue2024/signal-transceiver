"""API v1 package - RESTful API endpoints."""
from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.data import router as data_router
from src.api.v1.subscription import router as subscription_router
from src.api.v1.client import router as client_router
from src.api.v1.strategy import router as strategy_router
from src.api.v1.admin import router as admin_router
from src.api.v1.system import router as system_router
from src.api.v1.compliance import router as compliance_router
from src.api.v1.analytics import router as analytics_router
from src.api.v1.webhooks import router as webhooks_router
from src.api.v1.feedback import router as feedback_router
from src.api.v1.notifications import router as notifications_router
from src.api.v1.notifications import export_router
from src.api.v1.config_logs import config_router, logs_router
from src.api.v1.transform import router as transform_router
# Import module uses Python keyword 'import', so we use dynamic import
import importlib
try:
    import_module = importlib.import_module('src.api.v1.import')
    import_router = import_module.router
    HAS_IMPORT = True
except (ImportError, AttributeError):
    import_router = None
    HAS_IMPORT = False

# Create main v1 router
router = APIRouter()

# Include all routers
router.include_router(auth_router)
router.include_router(data_router)
router.include_router(subscription_router)
router.include_router(client_router)
router.include_router(strategy_router)
router.include_router(admin_router)
router.include_router(system_router)
router.include_router(compliance_router)
router.include_router(analytics_router)
router.include_router(webhooks_router)
router.include_router(feedback_router)
router.include_router(notifications_router)
router.include_router(export_router)
router.include_router(config_router)
router.include_router(logs_router)
router.include_router(transform_router)
if HAS_IMPORT and import_router:
    router.include_router(import_router)

__all__ = ["router"]
