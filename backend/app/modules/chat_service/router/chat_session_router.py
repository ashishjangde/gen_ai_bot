from uuid import UUID
from fastapi import APIRouter, Depends
from app.modules.chat_service.service.chat_session_service import (
    ChatSessionService,
    get_chat_session_service,
)
from app.modules.chat_service.schema.chat_session_schema import (
    CreateChatSessionSchema,
    UpdateChatSessionSchema,
    ChatSessionResponseSchema,
    ChatSessionListResponseSchema,
)
from app.schema.message_schema import MessageSchema
from app.advices.response import SuccessResponseSchema, ErrorResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


@router.post(
    "/sessions",
    summary="Create new chat session",
    response_model=SuccessResponseSchema[ChatSessionResponseSchema],
    responses={
        200: {
            "description": "Session created successfully",
            "model": SuccessResponseSchema[ChatSessionResponseSchema]
        },
        401: {
            "description": "Unauthorized",
            "model": ErrorResponseSchema
        }
    }
)
async def create_session(
    data: CreateChatSessionSchema,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service)
):
    """Create a new chat session for the authenticated user"""
    result = await service.create_session(current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/sessions",
    summary="List user's chat sessions",
    response_model=SuccessResponseSchema[list[ChatSessionListResponseSchema]],
)
async def list_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service)
):
    """Get all chat sessions for the authenticated user with message counts"""
    result = await service.get_user_sessions(current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/sessions/{session_id}",
    summary="Get session details",
    response_model=SuccessResponseSchema[ChatSessionResponseSchema],
    responses={
        200: {
            "description": "Session retrieved successfully",
            "model": SuccessResponseSchema[ChatSessionResponseSchema]
        },
        404: {
            "description": "Session not found",
            "model": ErrorResponseSchema
        },
        403: {
            "description": "User doesn't own this session",
            "model": ErrorResponseSchema
        }
    }
)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service)
):
    """Get details of a specific chat session"""
    result = await service.get_session(session_id, current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.put(
    "/sessions/{session_id}",
    summary="Update session title",
    response_model=SuccessResponseSchema[ChatSessionResponseSchema],
)
async def update_session(
    session_id: UUID,
    data: UpdateChatSessionSchema,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service)
):
    """Update the title of a chat session"""
    result = await service.update_session(session_id, current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.delete(
    "/sessions/{session_id}",
    summary="Delete chat session",
    response_model=SuccessResponseSchema[MessageSchema],
)
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service)
):
    """Delete a chat session and all its messages"""
    await service.delete_session(session_id, current_user.id)
    return BaseResponseHandler.success_response(data={"message": "Session deleted successfully"})
