from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from app.modules.chat_service.schema.chat_schema import ChatMessageSchema, ChatSourceSchema


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    title: str | None = Field(None, max_length=255)


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""
    title: str | None = Field(None, max_length=255)


class ChatSessionSchema(BaseModel):
    """Schema for returning chat session"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


# Define message/source schemas inline to avoid circular imports
class ChatMessageInSession(BaseModel):
    """Inline message schema for session responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: list[dict[str, Any]] | None = None
    created_at: datetime


class ChatSourceInSession(BaseModel):
    """Inline source schema for session responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    user_id: UUID
    source_type: str
    title: str | None
    original_filename: str | None
    url: str | None
    status: str
    extra_data: dict[str, Any] | None = None
    created_at: datetime


class ChatSessionWithMessagesSchema(ChatSessionSchema):
    """Schema for returning chat session with messages"""
    messages: list[ChatMessageInSession] = []
    sources: list[ChatSourceInSession] = []
