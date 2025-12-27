from fastapi import APIRouter, Depends
from app.modules.user_service.schema.auth_schema import ReturnUserSchema
from app.modules.user_service.schema.user_schema import UpdateUserSchema, ChangePasswordSchema
from app.schema.message_schema import MessageSchema
from app.advices.response import SuccessResponseSchema, ErrorResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.modules.user_service.service.user_service import UserProfileService, get_user_profile_service
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


@router.get(
    "/me",
    summary="Get current user profile",
    response_model=SuccessResponseSchema[CurrentUser]
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user)
):
    return BaseResponseHandler.success_response(data=current_user)


@router.put(
    "/me",
    summary="Update current user profile",
    response_model=SuccessResponseSchema[ReturnUserSchema]
)
async def update_profile(
    data: UpdateUserSchema,
    current_user: CurrentUser = Depends(get_current_user),
    service: UserProfileService = Depends(get_user_profile_service)
):
    result = await service.update_profile(current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.post(
    "/me/change-password",
    summary="Change user password",
    response_model=SuccessResponseSchema[MessageSchema]
)
async def change_password(
    data: ChangePasswordSchema,
    current_user: CurrentUser = Depends(get_current_user),
    service: UserProfileService = Depends(get_user_profile_service)
):
    await service.change_password(current_user.id, data)
    return BaseResponseHandler.success_response(data={"message": "Password changed successfully"})


@router.delete(
    "/me",
    summary="Delete user account",
    response_model=SuccessResponseSchema[MessageSchema]
)
async def delete_account(
    current_user: CurrentUser = Depends(get_current_user),
    service: UserProfileService = Depends(get_user_profile_service)
):
    await service.delete_account(current_user.id)
    return BaseResponseHandler.success_response(data={"message": "Account deleted successfully"})
