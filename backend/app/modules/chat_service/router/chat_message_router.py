from uuid import UUID
from fastapi import APIRouter, Depends
from app.modules.chat_service.service.chat_message_service import (
    ChatMessageService,
    get_chat_message_service,
)
from app.modules.chat_service.schema.chat_message_schema import (
    SendMessageSchema,
    ChatMessageWithSourcesSchema,
    ChatConversationResponseSchema,
)
from app.advices.response import SuccessResponseSchema, ErrorResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


@router.post(
    "/sessions/{session_id}/messages",
    summary="Send message in chat session",
    response_model=SuccessResponseSchema[dict],
    responses={
        200: {
            "description": "Message sent and response generated",
            "model": SuccessResponseSchema[dict]
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
async def send_message(
    session_id: UUID,
    data: SendMessageSchema,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatMessageService = Depends(get_chat_message_service)
):
    """
    Send a message in a chat session and receive AI response with RAG context.
    Returns both the user message and assistant response.
    """
    result = await service.send_message(session_id, current_user.id, data)
    return BaseResponseHandler.success_response(data=result)


@router.get(
    "/sessions/{session_id}/messages",
    summary="Get conversation history",
    response_model=SuccessResponseSchema[ChatConversationResponseSchema],
    responses={
        200: {
            "description": "Conversation history retrieved",
            "model": SuccessResponseSchema[ChatConversationResponseSchema]
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
async def get_conversation_history(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatMessageService = Depends(get_chat_message_service)
):
    """Get full conversation history for a chat session with source references"""
    result = await service.get_conversation_history(session_id, current_user.id)
    return BaseResponseHandler.success_response(data=result)
