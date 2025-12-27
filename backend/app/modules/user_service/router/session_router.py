from uuid import UUID
from fastapi import APIRouter, Depends, Cookie
from app.modules.user_service.schema.session_schema import SessionListSchema
from app.schema.message_schema import MessageSchema
from app.advices.response import SuccessResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.modules.user_service.service.session_service import SessionService, get_session_service
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


@router.get(
    "/",
    summary="Get all user sessions",
    response_model=SuccessResponseSchema[SessionListSchema]
)
async def get_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    result = await service.get_user_sessions(current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.delete(
    "/{session_id}",
    summary="Revoke a specific session",
    response_model=SuccessResponseSchema[MessageSchema]
)
async def revoke_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    await service.revoke_session(current_user.id, session_id)
    return BaseResponseHandler.success_response(data={"message": "Session revoked successfully"})


@router.delete(
    "/",
    summary="Revoke all sessions except current",
    response_model=SuccessResponseSchema[MessageSchema]
)
async def revoke_all_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    refresh_token: str = Cookie(None),
    service: SessionService = Depends(get_session_service)
):
    await service.revoke_all_sessions(current_user.id, refresh_token)
    return BaseResponseHandler.success_response(data={"message": "All other sessions revoked successfully"})
