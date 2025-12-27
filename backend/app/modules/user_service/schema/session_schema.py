from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class SessionSchema(BaseModel):
    """Schema for returning session information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_agent: str | None = None
    ip_address: str | None = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class SessionListSchema(BaseModel):
    """Schema for listing sessions"""
    sessions: list[SessionSchema]
    total: int
