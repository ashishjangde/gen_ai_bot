from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Literal


class ChatMessageCreate(BaseModel):
    """Schema for sending a new message"""
    content: str = Field(..., min_length=1, max_length=10000)
    # Agent automatically decides which tools to use (RAG, memory, web search)


class ChatMessageSchema(BaseModel):
    """Schema for returning chat message"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    role: str  # 'user', 'assistant', 'system'
    content: str
    sources: list[dict[str, Any]] | None = None
    created_at: datetime


class ChatSourceCreate(BaseModel):
    """Schema for creating a source (web scrape)"""
    url: str = Field(..., max_length=2048)


class ChatSourceSchema(BaseModel):
    """Schema for returning chat source"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: UUID
    user_id: UUID
    source_type: str  # 'pdf', 'csv', 'web'
    title: str | None
    original_filename: str | None
    url: str | None
    status: str  # 'processing', 'ready', 'failed'
    extra_data: dict[str, Any] | None = None
    created_at: datetime


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    id: UUID
    source_type: str
    title: str | None
    original_filename: str | None
    url: str | None
    status: str
    message: str


class StreamingChunk(BaseModel):
    """Schema for SSE streaming response chunks"""
    type: str  # 'content', 'sources', 'done', 'error'
    content: str | None = None
    sources: list[dict[str, Any]] | None = None
    error: str | None = None

