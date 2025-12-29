"""
Chat Service - Orchestrates messaging and file uploads

Key features:
- Agent automatically decides which tools to use (no manual toggle)
- Token-efficient: Agent fetches context only when needed
- Scalable: Background processing for file uploads
"""
import uuid
import os
from uuid import UUID
from typing import AsyncGenerator
from fastapi import Depends, UploadFile

from app.modules.chat_service.repositories.chat_sessions_repository import ChatSessionRepository
from app.modules.chat_service.repositories.chat_repository import ChatMessageRepository
from app.modules.chat_service.repositories.chat_source_repository import ChatSourceRepository
from app.modules.chat_service.services.memory_service import MemoryService
from app.modules.chat_service.services.agent_service import run_chat_agent
from app.modules.chat_service.schema.chat_schema import (
    ChatMessageCreate, ChatSourceSchema, StreamingChunk, FileUploadResponse
)
from app.config.rq_config import get_queue, QUEUE_DOCUMENTS
from app.config.oci_storage import OCIStorageService
from app.config.settings import settings
from app.config.logging import get_logger
from app.exceptions.exceptions import ResourceNotFoundException

logger = get_logger("app.chat.service")


# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".txt": "txt",
    ".md": "txt",
    ".json": "json",
}


def get_source_type(filename: str) -> str | None:
    ext = os.path.splitext(filename)[1].lower()
    return ALLOWED_EXTENSIONS.get(ext)


class ChatService:
    """Main chat service - messaging and file management"""
    
    def __init__(
        self,
        session_repo: ChatSessionRepository,
        message_repo: ChatMessageRepository,
        source_repo: ChatSourceRepository,
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.source_repo = source_repo
    
    # ============ Messaging ============
    
    async def send_message(
        self,
        session_id: UUID,
        user_id: UUID,
        data: ChatMessageCreate,
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Send a message and stream the response.
        
        Agent autonomously decides:
        - Whether to search documents (RAG)
        - Whether to check user memory (LTM)
        - Whether to search the web
        - Whether to use calculator/datetime
        
        This is token-efficient: agent only fetches context when needed.
        """
        # Verify session
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            yield StreamingChunk(type="error", error="Session not found")
            return
        
        # Save user message
        await self.message_repo.create(
            session_id=session_id,
            role="user",
            content=data.content,
            commit=True,
        )
        
        # Update STM (for conversation flow)
        await MemoryService.update_stm(session_id, "user", data.content)
        
        # Get recent conversation for context
        stm_messages = await MemoryService.ShortTermMemory.get_session_messages(session_id)
        
        # Run agent - it decides what tools to use
        try:
            response_text, sources = await run_chat_agent(
                query=data.content,
                user_id=str(user_id),
                session_id=str(session_id),
                context_messages=stm_messages,
            )
            
            # Stream response in chunks
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                yield StreamingChunk(type="content", content=response_text[i:i + chunk_size])
            
            # Send sources if any tools were used
            if sources:
                yield StreamingChunk(type="sources", sources=sources)
            
            # Save assistant message
            await self.message_repo.create(
                session_id=session_id,
                role="assistant",
                content=response_text,
                sources=sources if sources else None,
                commit=True,
            )
            
            # Update STM
            await MemoryService.update_stm(session_id, "assistant", response_text)
            
            yield StreamingChunk(type="done")
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            yield StreamingChunk(type="error", error=str(e))
    
    # ============ File Upload ============
    
    async def upload_file(
        self,
        session_id: UUID,
        user_id: UUID,
        file: UploadFile,
    ) -> FileUploadResponse:
        """
        Upload a file (PDF, CSV, TXT, JSON).
        Files are processed in background and made available for RAG.
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        filename = file.filename or "unknown"
        source_type = get_source_type(filename)
        if not source_type:
            raise ValueError(f"Unsupported file. Allowed: {list(ALLOWED_EXTENSIONS.keys())}")
        
        content = await file.read()
        
        # Upload to OCI if configured
        file_url = None
        object_name = None
        
        if settings.oci_namespace and settings.oci_bucket_name:
            try:
                upload_result = OCIStorageService.upload_file(
                    file_content=content,
                    filename=filename,
                    content_type=file.content_type or "application/octet-stream",
                    folder=f"sessions/{session_id}",
                )
                file_url = upload_result["url"]
                object_name = upload_result["object_name"]
            except Exception as e:
                logger.warning(f"OCI upload failed: {e}")
        
        # Create record
        collection_name = f"{source_type}_{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"
        
        source = await self.source_repo.create(
            session_id=session_id,
            user_id=user_id,
            source_type=source_type,
            title=filename,
            original_filename=filename,
            url=file_url,
            qdrant_collection=collection_name,
            status="processing",
            extra_data={"oci_object_name": object_name} if object_name else None,
            commit=True,
        )
        
        # Queue processing
        queue = get_queue(QUEUE_DOCUMENTS)
        job_map = {
            "pdf": "process_pdf_job",
            "csv": "process_csv_job",
            "txt": "process_text_job",
            "json": "process_text_job",
        }
        job_name = f"app.modules.chat_service.jobs.document_jobs.{job_map[source_type]}"
        
        if object_name:
            queue.enqueue(job_name, str(source.id), object_name, str(user_id), str(session_id), collection_name, True)
        else:
            import tempfile
            file_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}_{filename}")
            with open(file_path, "wb") as f:
                f.write(content)
            queue.enqueue(job_name, str(source.id), file_path, str(user_id), str(session_id), collection_name, False)
        
        return FileUploadResponse(
            id=source.id,
            source_type=source_type,
            title=filename,
            original_filename=filename,
            url=file_url,
            status="processing",
            message=f"Processing {source_type.upper()} file...",
        )
    
    # ============ Web Scraping ============
    
    async def scrape_web(
        self,
        session_id: UUID,
        user_id: UUID,
        url: str,
    ) -> ChatSourceSchema:
        """Scrape a web page and add as RAG source"""
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        collection_name = f"web_{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"
        
        source = await self.source_repo.create(
            session_id=session_id,
            user_id=user_id,
            source_type="web",
            title=url,
            url=url,
            qdrant_collection=collection_name,
            status="processing",
            commit=True,
        )
        
        queue = get_queue(QUEUE_DOCUMENTS)
        queue.enqueue(
            "app.modules.chat_service.jobs.document_jobs.scrape_web_job",
            str(source.id), url, str(user_id), str(session_id), collection_name,
        )
        
        return ChatSourceSchema.model_validate(source)
    
    # ============ Sources ============
    
    async def get_sources(self, session_id: UUID, user_id: UUID) -> list[ChatSourceSchema]:
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        sources = await self.source_repo.get_by_session_id(session_id)
        return [ChatSourceSchema.model_validate(s) for s in sources]
    
    async def delete_source(self, source_id: UUID, user_id: UUID) -> bool:
        source = await self.source_repo.get_by_id(source_id)
        if not source or source.user_id != user_id:
            raise ResourceNotFoundException("Source not found")
        
        if source.extra_data and source.extra_data.get("oci_object_name"):
            try:
                OCIStorageService.delete_file(source.extra_data["oci_object_name"])
            except Exception:
                pass
        
        await self.source_repo.delete(id=source_id, commit=True)
        return True


def get_chat_service(
    session_repo: ChatSessionRepository = Depends(ChatSessionRepository),
    message_repo: ChatMessageRepository = Depends(ChatMessageRepository),
    source_repo: ChatSourceRepository = Depends(ChatSourceRepository),
) -> ChatService:
    return ChatService(session_repo, message_repo, source_repo)
