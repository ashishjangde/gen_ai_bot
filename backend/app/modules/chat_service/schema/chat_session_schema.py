from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CreateChatSessionSchema(BaseModel):
    """Schema for creating a new chat session"""
    title: str | None = Field(None, max_length=255, description="Optional session title")


class UpdateChatSessionSchema(BaseModel):
    """Schema for updating a chat session"""
    title: str = Field(..., min_length=1, max_length=255, description="Session title")


class ChatSessionResponseSchema(BaseModel):
    """Schema for chat session response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponseSchema(BaseModel):
    """Schema for listing chat sessions with message count"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(0, description="Number of messages in the session")
