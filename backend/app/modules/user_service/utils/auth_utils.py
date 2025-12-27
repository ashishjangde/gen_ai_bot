from datetime import UTC, datetime, timedelta
from jose import JWTError, jwt
from fastapi import Response
from app.config.settings import settings


class JWTUtils:
    REFRESH_TOKEN_SECRET_KEY = settings.refresh_token_secret_key
    ACCESS_TOKEN_SECRET_KEY = settings.access_token_secret_key
    ALGORITHM = settings.jwt_algorithms
    REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

    @staticmethod
    def create_access_token(data: dict[str, str] = None) -> str:
        to_encode = data.copy() if data else {}
        expire = datetime.now(UTC) + timedelta(
            minutes=JWTUtils.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, JWTUtils.ACCESS_TOKEN_SECRET_KEY, algorithm=JWTUtils.ALGORITHM
        )

    @staticmethod
    def decode_access_token(token: str) -> dict[str, str] | None:
        try:
            payload = jwt.decode(
                token, JWTUtils.ACCESS_TOKEN_SECRET_KEY, algorithms=[JWTUtils.ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def verify_access_token(token: str) -> bool:
        try:
            jwt.decode(
                token, JWTUtils.ACCESS_TOKEN_SECRET_KEY, algorithms=[JWTUtils.ALGORITHM]
            )
            return True
        except JWTError:
            return False

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a secure refresh token"""
        payload = {
            "sub": user_id,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC)
            + timedelta(minutes=JWTUtils.REFRESH_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(
            payload, JWTUtils.REFRESH_TOKEN_SECRET_KEY, algorithm=JWTUtils.ALGORITHM
        )

    @staticmethod
    def decode_refresh_token(token: str) -> dict[str, str] | None:
        try:
            payload = jwt.decode(
                token,
                JWTUtils.REFRESH_TOKEN_SECRET_KEY,
                algorithms=[JWTUtils.ALGORITHM],
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def verify_refresh_token(token: str) -> bool:
        try:
            jwt.decode(
                token,
                JWTUtils.REFRESH_TOKEN_SECRET_KEY,
                algorithms=[JWTUtils.ALGORITHM],
            )
            return True
        except JWTError:
            return False

    @staticmethod
    def get_token_expiry_time() -> datetime:
        """Get the expiry time for access tokens"""
        return datetime.now(UTC) + timedelta(
            minutes=JWTUtils.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    @staticmethod
    def get_refresh_token_expiry_time() -> datetime:
        """Get the expiry time for refresh tokens"""
        return datetime.now(UTC) + timedelta(
            minutes=JWTUtils.REFRESH_TOKEN_EXPIRE_MINUTES
        )


class VerificationCodeUtils:
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a random 6-digit verification code."""
        import random

        return str(random.randint(100000, 999999))

    @staticmethod
    def verification_code_expiry() -> datetime:
        """Get expiry time for verification codes (15 minutes from now)"""
        return datetime.now(UTC) + timedelta(minutes=15)

    @staticmethod
    def is_verification_code_expired(expiry_time: datetime) -> bool:
        """Check if verification code has expired"""
        return datetime.now(UTC) > expiry_time


class CookieUtils:
    @staticmethod
    def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
        """Set HTTP-only cookies for authentication tokens"""
        # Set access token cookie (short-lived)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=settings.access_token_expire_minutes * 60,
            httponly=True,
            secure=settings.env == "production",
            samesite="lax",
            path="/",
        )
        # Set refresh token cookie (long-lived)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=settings.refresh_token_expire_minutes * 60,
            httponly=True,
            secure=settings.env == "production",
            samesite="lax",
            path="/",
        )

    @staticmethod
    def clear_auth_cookies(response: Response) -> None:
        """Clear authentication cookies"""
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")