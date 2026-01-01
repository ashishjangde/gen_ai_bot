"""
API v1 router - combines all endpoints.
"""

from fastapi import APIRouter

from mvp.app.api.v1.auth import router as auth_router
from mvp.app.api.v1.chat import router as chat_router
from mvp.app.api.v1.files import router as files_router
from mvp.app.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")

# Include all routers
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(files_router)
router.include_router(health_router)
