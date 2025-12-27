from fastapi import Depends
from app.modules.user_service.schema.auth_schema import (
    VerifySchema, RegisterSchema, LoginSchema, ForgotPasswordSchema, 
    ResetPasswordSchema, ReturnUserSchema, TokenResponseSchema, RefreshTokenResponseSchema
)
from app.modules.user_service.repositories.user_repository import UserRepository
from app.modules.user_service.models.user_model import User
from app.modules.user_service.utils.security import get_password_hash, verify_password
from app.exceptions.exceptions import (
    InvalidCredentialsException,
    InvalidOperationException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    UnauthorizedAccessException,
    ResourceNotVerifiedException,
    VerificationCodeExpiredException,
)
from app.modules.user_service.utils.auth_utils import JWTUtils, VerificationCodeUtils
from datetime import datetime, UTC
from app.modules.user_service.repositories.session_repository import SessionRepository


class UserService:
    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository) -> None:
        self.user_repository = user_repository
        self.session_repository = session_repository
    
    async def register(self, data: RegisterSchema) -> ReturnUserSchema:
        user = await self.user_repository.get_by_email(data.email)
        if user and user.is_verified:
            raise ResourceAlreadyExistsException("Email already registered")

        hashed_password = get_password_hash(data.password)
        verification_code = VerificationCodeUtils.generate_verification_code()
        verification_code_expiry = VerificationCodeUtils.verification_code_expiry()
        
        if user and not user.is_verified:
            user = await self.user_repository.update(
                id=user.id,
                name=data.name,
                password=hashed_password,
                verification_code=verification_code,
                verification_code_expiry=verification_code_expiry,
                commit=True
            )
        else:
            user = await self.user_repository.create(
                name=data.name,
                email=data.email,
                password=hashed_password,
                verification_code=verification_code,
                verification_code_expiry=verification_code_expiry,
                commit=True
            )
        
        return ReturnUserSchema.model_validate(user)
    
    async def login(self, data: LoginSchema) -> TokenResponseSchema:
        user = await self.user_repository.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password):
            raise InvalidCredentialsException("Invalid credentials")
        if not user.is_verified:
            raise ResourceNotVerifiedException(f"User not verified with this email {data.email}")
        
        access_token = JWTUtils.create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "name": user.name
        })
        refresh_token = JWTUtils.create_refresh_token(user_id=str(user.id))
        
        await self.session_repository.enforce_session_limit(user_id=user.id, limit=3)
        
        await self.session_repository.create(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=JWTUtils.get_refresh_token_expiry_time(),
            commit=True
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            user=ReturnUserSchema.model_validate(user)
        )
    
    async def verify_user(self, data: VerifySchema) -> TokenResponseSchema:
        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise ResourceNotFoundException("User not found")
        if user.is_verified:
            raise InvalidOperationException("User already verified")
        if VerificationCodeUtils.is_verification_code_expired(user.verification_code_expiry):
            raise VerificationCodeExpiredException("Verification code expired")
        if user.verification_code != data.verification_code: 
            raise InvalidOperationException("Invalid verification code")

        user = await self.user_repository.update(
            id=user.id, 
            is_verified=True, 
            verification_code=None, 
            verification_code_expiry=None, 
            commit=True
        )
        
        access_token = JWTUtils.create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "name": user.name
        })
        refresh_token = JWTUtils.create_refresh_token(user_id=str(user.id))
        
        await self.session_repository.enforce_session_limit(user_id=user.id, limit=3)
        
        await self.session_repository.create(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=JWTUtils.get_refresh_token_expiry_time(),
            commit=True
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            user=ReturnUserSchema.model_validate(user)
        )
    
    async def refresh_token(self, refresh_token: str) -> RefreshTokenResponseSchema:
        payload = JWTUtils.decode_refresh_token(refresh_token)
        if not payload:
            raise UnauthorizedAccessException("Invalid refresh token")
            
        session = await self.session_repository.get_by_refresh_token(refresh_token)
        if not session:
            raise UnauthorizedAccessException("Session not found or expired")
            
        if session.expires_at < datetime.now(UTC):
            raise UnauthorizedAccessException("Session has expired")
        
        user = await self.user_repository.get_by_id(session.user_id)
        if not user:
            raise ResourceNotFoundException("User not found")

        access_token = JWTUtils.create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "name": user.name
        })
        
        return RefreshTokenResponseSchema(
            access_token=access_token,
            user=ReturnUserSchema.model_validate(user)
        )

    async def forgot_password(self, data: ForgotPasswordSchema) -> bool:
        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise ResourceNotFoundException("User not found")
        if not user.is_verified:
            raise ResourceNotVerifiedException("User not verified")
        
        verification_code = VerificationCodeUtils.generate_verification_code()
        verification_code_expiry = VerificationCodeUtils.verification_code_expiry()
        
        await self.user_repository.update(
            id=user.id,
            verification_code=verification_code,
            verification_code_expiry=verification_code_expiry,
            commit=True
        )
        # TODO: send mail
        return True
    
    async def logout(self, refresh_token: str) -> bool:
        if refresh_token is not None:
            await self.session_repository.delete_by_refresh_token(refresh_token)
        return True

    async def reset_password(self, data: ResetPasswordSchema) -> bool:
        """Reset user password after verification"""
        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise ResourceNotFoundException("User not found")
        if not user.is_verified:
            raise ResourceNotVerifiedException("User not verified")
        if VerificationCodeUtils.is_verification_code_expired(user.verification_code_expiry):
            raise VerificationCodeExpiredException("Verification code expired")
        if user.verification_code != data.verification_code:
            raise InvalidOperationException("Invalid verification code")
        
        hashed_password = get_password_hash(data.password)
        await self.user_repository.update(
            id=user.id,
            password=hashed_password,
            verification_code=None,
            verification_code_expiry=None,
            commit=True
        )
        return True

    async def verify_code_valid(self, email: str, code: str) -> bool:
        """Verify if a code is valid for password reset"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise ResourceNotFoundException("User not found")
        if VerificationCodeUtils.is_verification_code_expired(user.verification_code_expiry):
            raise VerificationCodeExpiredException("Verification code expired")
        if user.verification_code != code:
            raise InvalidOperationException("Invalid verification code")
        return True


def get_user_service(
    user_repository: UserRepository = Depends(UserRepository),
    session_repository: SessionRepository = Depends(SessionRepository)
) -> UserService:
    return UserService(user_repository, session_repository)