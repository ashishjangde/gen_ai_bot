"""
Pydantic schemas for File API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    id: UUID
    filename: str
    source_type: str
    status: str  # 'processing', 'ready', 'failed'
    created_at: datetime

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """File/source details."""
    id: UUID
    source_type: str
    title: Optional[str]
    original_filename: Optional[str]
    status: str
    created_at: datetime
    extra_data: Optional[dict] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """List of files for a session/user."""
    files: list[FileResponse]
    total: int
