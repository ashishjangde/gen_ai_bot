from uuid import UUID
from fastapi import APIRouter, Depends
from app.modules.chat_service.schema.chat_session_schema import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionSchema, ChatSessionWithMessagesSchema
)
from app.modules.chat_service.schema.chat_schema import ChatMessageSchema
from app.schema.message_schema import MessageSchema
from app.advices.response import SuccessResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.modules.chat_service.services.chat_session_service import (
    ChatSessionService, get_chat_session_service
)
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


@router.post(
    "/",
    summary="Create a new chat session",
    response_model=SuccessResponseSchema[ChatSessionSchema],
)
async def create_session(
    data: ChatSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    result = await service.create_session(current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/",
    summary="Get all chat sessions",
    response_model=SuccessResponseSchema[list[ChatSessionSchema]],
)
async def get_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    result = await service.get_sessions(current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/{session_id}",
    summary="Get a chat session with messages",
    response_model=SuccessResponseSchema[ChatSessionWithMessagesSchema],
)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    result = await service.get_session(session_id, current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/{session_id}/messages",
    summary="Get all messages for a session",
    response_model=SuccessResponseSchema[list[ChatMessageSchema]],
)
async def get_session_messages(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    result = await service.get_session_messages(session_id, current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.put(
    "/{session_id}",
    summary="Update a chat session",
    response_model=SuccessResponseSchema[ChatSessionSchema],
)
async def update_session(
    session_id: UUID,
    data: ChatSessionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    result = await service.update_session(session_id, current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.delete(
    "/{session_id}",
    summary="Delete a chat session",
    response_model=SuccessResponseSchema[MessageSchema],
)
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatSessionService = Depends(get_chat_session_service),
):
    await service.delete_session(session_id, current_user.id)
    return BaseResponseHandler.success_response(data={"message": "Session deleted successfully"})
