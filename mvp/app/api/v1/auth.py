"""
Authentication API endpoints.
"""

import hashlib
import secrets
import logging
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mvp.app.db.database import get_async_session
from mvp.app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from mvp.app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Simple token storage (in production use JWT or Redis)
# Format: {token: {user_id, expires_at}}
_tokens: dict[str, dict] = {}


def _hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return _hash_password(password) == hashed


def _generate_token(user_id: UUID) -> str:
    """Generate a simple access token."""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "user_id": user_id,
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }
    return token


async def get_current_user(
    token: str,
    db: AsyncSession = Depends(get_async_session),
) -> UUID:
    """Dependency to get current user from token."""
    token_data = _tokens.get(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    if datetime.utcnow() > token_data["expires_at"]:
        del _tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    return token_data["user_id"]


# =============================================================================
# Auth Endpoints
# =============================================================================
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegister,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Register a new user.
    
    Returns access token on success.
    """
    repo = UserRepository(db)
    
    # Check if email exists
    existing = await repo.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await repo.create(
        email=request.email,
        password_hash=_hash_password(request.password),
        name=request.name,
    )
    
    # Generate token
    token = _generate_token(user.id)
    
    logger.info(f"User registered: {user.email}")
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Login with email and password.
    
    Returns access token on success.
    """
    repo = UserRepository(db)
    
    # Find user
    user = await repo.get_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not _verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate token
    token = _generate_token(user.id)
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    token: str,
    db: AsyncSession = Depends(get_async_session),
):
    """Get current user profile."""
    user_id = await get_current_user(token, db)
    
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
