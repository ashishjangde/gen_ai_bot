"""
File upload and management API endpoints.

Files are processed by RQ workers in separate processes for scalability.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from mvp.app.db.database import get_async_session
from mvp.app.schemas.file import FileUploadResponse, FileResponse, FileListResponse
from mvp.app.repositories.chat_source_repository import ChatSourceRepository
from mvp.app.queues.queue_manager import enqueue_job, get_job_status
from mvp.app.queues.tasks import process_file_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


# =============================================================================
# File Endpoints
# =============================================================================
@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session_id: UUID,
    user_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Upload a file for RAG processing.
    
    Supported formats: PDF, CSV, XLSX, TXT, MD
    
    The file is:
    1. Saved to database with 'processing' status
    2. Enqueued to RQ for background processing by workers
    3. Workers will: upload to S3, chunk, embed, store in Qdrant
    4. Status updated to 'ready' when complete
    """
    # Validate file type
    filename = file.filename or "unknown"
    extension = filename.split(".")[-1].lower()
    
    supported_types = {"pdf", "csv", "xlsx", "txt", "md"}
    if extension not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(supported_types)}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Create source record
        source_repo = ChatSourceRepository(db)
        source = await source_repo.create(
            session_id=session_id,
            user_id=user_id,
            source_type=extension,
            title=filename,
            original_filename=filename,
            status="processing",
        )
        
        # Enqueue to RQ (processed by separate worker)
        job_id = enqueue_job(
            process_file_task,
            source_id=str(source.id),
            user_id=str(user_id),
            session_id=str(session_id),
            filename=filename,
            content=content,
            file_type=extension,
            priority="high",
        )
        
        logger.info(f"File {filename} enqueued to RQ, job_id={job_id}")
        
        return FileUploadResponse(
            id=source.id,
            filename=filename,
            source_type=extension,
            status="processing",
            created_at=source.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/job/{job_id}")
async def get_job_info(job_id: str):
    """Get the status of a file processing job."""
    status_info = get_job_status(job_id)
    return status_info


@router.get("", response_model=FileListResponse)
async def list_files(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """List all files for a session."""
    repo = ChatSourceRepository(db)
    files = await repo.get_by_session_id(session_id)
    
    return FileListResponse(
        files=[
            FileResponse(
                id=f.id,
                source_type=f.source_type,
                title=f.title,
                original_filename=f.original_filename,
                status=f.status,
                created_at=f.created_at,
                extra_data=f.extra_data,
            )
            for f in files
        ],
        total=len(files),
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get file details."""
    repo = ChatSourceRepository(db)
    file = await repo.get_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return FileResponse(
        id=file.id,
        source_type=file.source_type,
        title=file.title,
        original_filename=file.original_filename,
        status=file.status,
        created_at=file.created_at,
        extra_data=file.extra_data,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a file and its embeddings."""
    repo = ChatSourceRepository(db)
    file = await repo.get_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await repo.delete(file_id)
