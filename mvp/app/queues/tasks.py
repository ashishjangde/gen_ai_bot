"""
Background tasks for RQ workers.

IMPORTANT: These functions must be importable by the worker process.
They run in a SEPARATE process from FastAPI, so they:
- Cannot use FastAPI dependencies
- Must create their own database connections
- Must be fully synchronous (no async/await at top level)
"""

import logging
import asyncio
from uuid import UUID

logger = logging.getLogger(__name__)


def process_file_task(
    source_id: str,
    user_id: str,
    session_id: str,
    filename: str,
    content: bytes,
    file_type: str,
) -> dict:
    """
    Process and embed a file for RAG.
    
    This runs in a separate RQ worker process.
    
    Steps:
    1. Upload to object storage
    2. Parse and chunk document
    3. Generate embeddings
    4. Store in Qdrant
    5. Update source status in database
    
    Returns:
        {"success": bool, "message": str}
    """
    logger.info(f"[RQ Worker] Processing file: {filename} for user {user_id}")
    
    # Run async code in sync context
    result = asyncio.run(_process_file_async(
        source_id=source_id,
        user_id=user_id,
        session_id=session_id,
        filename=filename,
        content=content,
        file_type=file_type,
    ))
    
    return result


async def _process_file_async(
    source_id: str,
    user_id: str,
    session_id: str,
    filename: str,
    content: bytes,
    file_type: str,
) -> dict:
    """Async implementation of file processing."""
    from mvp.app.db.database import get_session_context
    from mvp.app.repositories.chat_source_repository import ChatSourceRepository
    from mvp.app.utils.object_service import ObjectService
    from mvp.app.utils.vector_service import VectorService
    from mvp.app.config.settings import settings
    
    try:
        # 1. Upload to object storage
        object_service = ObjectService(bucket=settings.supabase_bucket_name)
        await object_service.connect()
        
        object_key = f"users/{user_id}/sessions/{session_id}/{source_id}/{filename}"
        upload_success = await object_service.upload(content, object_key)
        
        if not upload_success:
            raise Exception("Failed to upload to object storage")
        
        logger.info(f"[RQ Worker] Uploaded {filename} to {object_key}")
        
        # 2. Process and embed
        vector_service = VectorService()
        await vector_service.connect()
        
        ingest_success = await vector_service.ingest_file(
            file_key=object_key,
            user_id=user_id,
            session_id=session_id,
        )
        
        await vector_service.close()
        await object_service.close()
        
        # 3. Update database status
        async with get_session_context() as db:
            repo = ChatSourceRepository(db)
            status = "ready" if ingest_success else "failed"
            await repo.update(
                UUID(source_id),
                status=status,
                url=object_key,
            )
        
        logger.info(f"[RQ Worker] File processed: {filename} -> {status}")
        
        return {"success": ingest_success, "message": f"File {filename} processed"}
        
    except Exception as e:
        logger.error(f"[RQ Worker] File processing failed: {filename} - {e}")
        
        # Update status to failed
        try:
            async with get_session_context() as db:
                repo = ChatSourceRepository(db)
                await repo.update(UUID(source_id), status="failed")
        except Exception as db_error:
            logger.error(f"[RQ Worker] Failed to update status: {db_error}")
        
        return {"success": False, "message": str(e)}


def update_embeddings_task(user_id: str, file_ids: list[str]) -> dict:
    """
    Re-embed files for a user.
    Useful for model updates or re-indexing.
    
    Returns:
        {"success": bool, "processed": int}
    """
    logger.info(f"[RQ Worker] Re-embedding {len(file_ids)} files for user {user_id}")
    
    # TODO: Implement re-embedding logic
    return {"success": True, "processed": len(file_ids)}
