from uuid import UUID
from fastapi import Depends
from app.modules.user_service.schema.auth_schema import ReturnUserSchema
from app.modules.user_service.schema.user_schema import UpdateUserSchema, ChangePasswordSchema
from app.modules.user_service.repositories.user_repository import UserRepository
from app.modules.user_service.utils.security import get_password_hash, verify_password
from app.exceptions.exceptions import (
    InvalidCredentialsException,
    ResourceNotFoundException,
)


class UserProfileService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository
    
    async def get_current_user(self, user_id: UUID) -> ReturnUserSchema:
        """Get current user profile"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        return ReturnUserSchema.model_validate(user)
    
    async def update_profile(self, user_id: UUID, data: UpdateUserSchema) -> ReturnUserSchema:
        """Update user profile"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        
        if update_data:
            user = await self.user_repository.update(id=user_id, commit=True, **update_data)
        
        return ReturnUserSchema.model_validate(user)
    
    async def change_password(self, user_id: UUID, data: ChangePasswordSchema) -> bool:
        """Change user password"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        
        if not verify_password(data.current_password, user.password):
            raise InvalidCredentialsException("Current password is incorrect")
        
        hashed_password = get_password_hash(data.new_password)
        await self.user_repository.update(id=user_id, password=hashed_password, commit=True)
        return True
    
    async def delete_account(self, user_id: UUID) -> bool:
        """Delete user account"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found")
        
        await self.user_repository.delete(id=user_id, commit=True)
        return True


def get_user_profile_service(
    user_repository: UserRepository = Depends(UserRepository),
) -> UserProfileService:
    return UserProfileService(user_repository)
