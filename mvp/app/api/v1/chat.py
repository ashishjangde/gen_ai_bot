"""
Chat API endpoints.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from mvp.app.db.database import get_async_session, get_session_context
from mvp.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    SessionDetailResponse,
    SessionListResponse,
    MessageResponse,
)
from mvp.app.repositories.chat_sessions_repository import ChatSessionRepository
from mvp.app.repositories.chat_repository import ChatMessageRepository
from mvp.app.services.chat_service import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# =============================================================================
# Chat Endpoints
# =============================================================================
@router.post("", response_class=StreamingResponse)
async def send_message(
    request: ChatRequest,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Send a message and get AI response (Streaming).
    """
    try:
        # Verify session exists
        session_repo = ChatSessionRepository(db)
        session = await session_repo.get_by_id(request.session_id)
        
        if not session or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        
        chat_service = await get_chat_service()
        
        # Generator for SSE
        async def event_generator():
            full_response = []
            collected_sources = []
            
            try:
                # Stream tokens
                async for event in chat_service.chat_stream(
                    message=request.message,
                    user_id=str(user_id),
                    session_id=str(request.session_id)
                ):
                    if event["event_type"] == "token":
                        token = event["content"]
                        full_response.append(token)
                        # Yield SSE format
                        yield f"data: {json.dumps({'content': token, 'type': 'token'})}\n\n"
                    elif event["event_type"] == "usage":
                        usage = event["content"]
                        yield f"data: {json.dumps({'usage': usage, 'type': 'usage'})}\n\n"
                    elif event["event_type"] == "source":
                        # Capture partial sources
                        sources_list = event["content"]
                        if isinstance(sources_list, list):
                            collected_sources.extend(sources_list)
                            # Yield sources to client
                            yield f"data: {json.dumps({'sources': sources_list, 'type': 'source'})}\n\n"
            
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            finally:
                # End of stream
                yield "data: [DONE]\n\n"
                
                # Fire & Forget Background Persistence
                # We do this here so we have the full accumulated text
                final_text = "".join(full_response)
                
                # Save to SQL (User + Assistant)
                # We need a new DB session since the dependency one might be closed or we want to be safe
                # Actually, for async, we should use a proper background worker pattern or 
                # just fire asyncio task. Since we are in an async generator, we can just fire it.
                # However, for SQL safety, we should probably let the Worker handle SQL or use a fresh/scoped session.
                # For this MVP, we will use the existing chat_service background method which handles Memory/Vector/Valkey.
                # But we ALSO need to save to the SQL ChatMessage table which was previously done in this endpoint.
                
                async def persist_all():
                    try:
                        # 1. Save to SQL
                        async with get_session_context() as task_db:
                            msg_repo = ChatMessageRepository(task_db)
                            await msg_repo.create(session_id=request.session_id, role="user", content=request.message)
                            await msg_repo.create(session_id=request.session_id, role="assistant", content=final_text)
                            
                        # 2. Save to Vector/Memory (via Service)
                        await chat_service.save_session_background(
                            user_id=str(user_id),
                            session_id=str(request.session_id),
                            user_message=request.message,
                            ai_response=final_text,
                            sources=collected_sources
                        )
                    except Exception as ex:
                        logger.error(f"Background persist failed: {ex}")

                import asyncio
                asyncio.create_task(persist_all())

        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Chat init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Session Endpoints
# =============================================================================
@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """List all chat sessions for the current user."""
    repo = ChatSessionRepository(db)
    sessions = await repo.get_by_user_id(user_id)
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages) if s.messages else 0,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreate,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new chat session."""
    repo = ChatSessionRepository(db)
    session = await repo.create(
        user_id=user_id,
        title=request.title or "New Chat",
    )
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a session with all messages."""
    session_repo = ChatSessionRepository(db)
    session = await session_repo.get_with_messages(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return SessionDetailResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a chat session and all its messages."""
    session_repo = ChatSessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await session_repo.delete(session_id)
