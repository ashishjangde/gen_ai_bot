from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ChatSourceResponseSchema(BaseModel):
    """Schema for message source response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    message_id: UUID
    source_type: str = Field(..., description="Type of source: pdf, web, db, tool")
    source_name: str = Field(..., description="Name or identifier of the source")
    chunk_id: str | None = Field(None, description="Chunk identifier from vector store")
    source_metadata: dict | None = Field(None, description="Additional metadata about the source")
