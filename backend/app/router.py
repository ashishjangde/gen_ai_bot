from fastapi import APIRouter
from app.modules.user_service.router.auth_router import router as auth_router
from app.modules.user_service.router.user_router import router as user_router
from app.modules.user_service.router.session_router import router as session_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(session_router, prefix="/sessions", tags=["Sessions"])

