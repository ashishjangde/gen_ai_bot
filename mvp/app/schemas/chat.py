"""
Pydantic schemas for Chat API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Chat Message Schemas
# =============================================================================
class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: UUID


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: str
    session_id: UUID
    intent: str  # What the router classified
    sources: list[dict] = []  # Sources used for RAG

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Single message in a session."""
    id: UUID
    role: str
    content: str
    sources: Optional[list[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Session Schemas
# =============================================================================
class SessionCreate(BaseModel):
    """Create a new chat session."""
    title: Optional[str] = None


class SessionResponse(BaseModel):
    """Chat session response."""
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    """Session with messages."""
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of sessions for a user."""
    sessions: list[SessionResponse]
    total: int
