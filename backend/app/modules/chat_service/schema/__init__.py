"""Chat service schemas"""

from app.modules.chat_service.schema.chat_session_schema import (
    CreateChatSessionSchema,
    UpdateChatSessionSchema,
    ChatSessionResponseSchema,
    ChatSessionListResponseSchema,
)
from app.modules.chat_service.schema.chat_message_schema import (
    SendMessageSchema,
    ChatMessageResponseSchema,
    ChatMessageWithSourcesSchema,
    ChatConversationResponseSchema,
)
from app.modules.chat_service.schema.chat_source_schema import (
    ChatSourceResponseSchema,
)

__all__ = [
    # Session schemas
    "CreateChatSessionSchema",
    "UpdateChatSessionSchema",
    "ChatSessionResponseSchema",
    "ChatSessionListResponseSchema",
    # Message schemas
    "SendMessageSchema",
    "ChatMessageResponseSchema",
    "ChatMessageWithSourcesSchema",
    "ChatConversationResponseSchema",
    # Source schemas
    "ChatSourceResponseSchema",
]
