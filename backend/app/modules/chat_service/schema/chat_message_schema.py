from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.modules.chat_service.models.chat_session_messages import MessageRole
from app.modules.chat_service.schema.chat_source_schema import ChatSourceResponseSchema


class SendMessageSchema(BaseModel):
    """Schema for sending a message in a chat session"""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")


class ChatMessageResponseSchema(BaseModel):
    """Schema for chat message response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class ChatMessageWithSourcesSchema(BaseModel):
    """Schema for message with source references"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime
    sources: list[ChatSourceResponseSchema] = Field(default_factory=list)


class ChatConversationResponseSchema(BaseModel):
    """Schema for full conversation history"""
    session_id: UUID
    messages: list[ChatMessageWithSourcesSchema]
