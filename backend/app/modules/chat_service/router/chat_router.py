from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File
from sse_starlette.sse import EventSourceResponse
from app.modules.chat_service.schema.chat_schema import (
    ChatMessageCreate, ChatSourceCreate, ChatSourceSchema, StreamingChunk, FileUploadResponse
)
from app.schema.message_schema import MessageSchema
from app.advices.response import SuccessResponseSchema
from app.advices.base_response_handler import BaseResponseHandler
from app.modules.chat_service.services.chat_service import ChatService, get_chat_service
from app.middlewares.dependencies import get_current_user, CurrentUser

router = APIRouter()


# ============ Message Routes ============

@router.post(
    "/sessions/{session_id}/messages",
    summary="Send a message and get streaming response",
)
async def send_message(
    session_id: UUID,
    data: ChatMessageCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Send a message and receive streaming response via Server-Sent Events.
    
    The AI agent automatically decides:
    - Whether to search your uploaded documents
    - Whether to query user memory
    - Whether to search the web for current info
    - Whether to use calculator or datetime
    
    Response stream format:
    - type: "content" with chunk of assistant response
    - type: "sources" with list of tools/sources used
    - type: "done" when complete
    - type: "error" if something went wrong
    """
    async def event_generator():
        async for chunk in service.send_message(session_id, current_user.id, data):
            yield {
                "event": chunk.type,
                "data": chunk.model_dump_json(),
            }
    
    return EventSourceResponse(event_generator())


# ============ Unified Upload Route ============

@router.post(
    "/sessions/{session_id}/upload",
    summary="Upload a file (PDF, CSV, TXT, MD, JSON)",
    response_model=SuccessResponseSchema[FileUploadResponse],
)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(..., description="File to upload (PDF, CSV, TXT, MD, JSON)"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Unified file upload endpoint.
    
    Supported file types:
    - **PDF**: Documents, reports, papers
    - **CSV**: Spreadsheet data
    - **TXT/MD**: Plain text, markdown files
    - **JSON**: Structured data
    
    Files are stored in Oracle Cloud Object Storage and processed in the background.
    """
    result = await service.upload_file(session_id, current_user.id, file)
    return BaseResponseHandler.success_response(data=result)


# ============ Web Scraping ============

@router.post(
    "/sessions/{session_id}/sources/web",
    summary="Scrape a web page",
    response_model=SuccessResponseSchema[ChatSourceSchema],
)
async def scrape_web(
    session_id: UUID,
    data: ChatSourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Scrape a web page and add it as a source.
    The page content will be extracted, chunked, and embedded for RAG.
    """
    result = await service.scrape_web(session_id, current_user.id, data.url)
    return BaseResponseHandler.success_response(data=result)


# ============ Source Management ============

@router.get(
    "/sessions/{session_id}/sources",
    summary="Get all sources for a session",
    response_model=SuccessResponseSchema[list[ChatSourceSchema]],
)
async def get_sources(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    result = await service.get_sources(session_id, current_user.id)
    return BaseResponseHandler.success_response(data=result)


@router.delete(
    "/sources/{source_id}",
    summary="Delete a source",
    response_model=SuccessResponseSchema[MessageSchema],
)
async def delete_source(
    source_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    await service.delete_source(source_id, current_user.id)
    return BaseResponseHandler.success_response(data={"message": "Source deleted"})
