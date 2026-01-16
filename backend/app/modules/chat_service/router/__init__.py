"""Chat service routers"""

from fastapi import APIRouter
from app.modules.chat_service.router.chat_session_router import router as session_router
from app.modules.chat_service.router.chat_message_router import router as message_router

# Combine all chat routers
router = APIRouter()

# Include session and message routers
router.include_router(session_router)
router.include_router(message_router)

__all__ = ["router"]
