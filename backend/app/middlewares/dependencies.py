from uuid import UUID
from fastapi import Depends, Header
from fastapi.security import APIKeyCookie, HTTPBearer
from pydantic import BaseModel
from app.modules.user_service.utils.auth_utils import JWTUtils
from app.exceptions.exceptions import UnauthorizedAccessException
from app.config.settings import settings

# Security schemes for Swagger UI - shows lock icon
access_token_cookie = APIKeyCookie(name="access_token", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """User data extracted from access token - no DB call needed"""
    id: UUID
    email: str
    name: str


async def get_access_token(
    cookie_token: str = Depends(access_token_cookie),
    authorization: str = Header(None, alias="Authorization"),
) -> str:
    """
    Get access token from either:
    - Cookie (works in both dev and production)
    - Bearer token in Authorization header (only in development)
    
    In production, only cookies work.
    In development, both cookies and bearer tokens work.
    """
    if cookie_token:
        return cookie_token
    if authorization and settings.env != "production":
        if authorization.startswith("Bearer "):
            return authorization[7:]
    raise UnauthorizedAccessException("Not authenticated")


async def get_current_user(
    access_token: str = Depends(get_access_token),
) -> CurrentUser:
    """
    Get current authenticated user from access token payload.
    NO database call - extracts user data directly from JWT.
    
    Token sources:
    - Cookie: Works in both dev and production
    - Bearer header: Only works in development
    """
    payload = JWTUtils.decode_access_token(access_token)
    if not payload or "sub" not in payload:
        raise UnauthorizedAccessException("Invalid or expired access token")
    
    try:
        return CurrentUser(
            id=UUID(payload["sub"]),
            email=payload.get("email", ""),
            name=payload.get("name", "")
        )
    except (ValueError, KeyError):
        raise UnauthorizedAccessException("Invalid token payload")


async def get_current_user_id(
    access_token: str = Depends(get_access_token),
) -> UUID:
    """
    Get current user ID from access token.
    Use this when you only need the user ID.
    """
    payload = JWTUtils.decode_access_token(access_token)
    if not payload or "sub" not in payload:
        raise UnauthorizedAccessException("Invalid or expired access token")
    
    try:
        return UUID(payload["sub"])
    except ValueError:
        raise UnauthorizedAccessException("Invalid token payload")
