from uuid import UUID
from fastapi import Depends
from app.modules.chat_service.repositories.chat_session_repository import ChatSessionRepository
from app.modules.chat_service.repositories.chat_message_repository import ChatMessageRepository
from app.modules.chat_service.repositories.chat_source_repository import ChatSourceRepository
from app.modules.chat_service.models.chat_session_messages import MessageRole
from app.modules.chat_service.schema.chat_message_schema import (
    SendMessageSchema,
    ChatMessageWithSourcesSchema,
    ChatConversationResponseSchema,
)
from app.modules.chat_service.schema.chat_source_schema import ChatSourceResponseSchema
from app.modules.chat_service.utils.vector_service import VectorService
from app.exceptions.exceptions import (
    ResourceNotFoundException,
    UnauthorizedAccessException,
)
from app.config.settings import settings


class ChatMessageService:
    """Service for handling chat messages with RAG integration"""
    
    def __init__(
        self,
        session_repository: ChatSessionRepository = Depends(ChatSessionRepository),
        message_repository: ChatMessageRepository = Depends(ChatMessageRepository),
        source_repository: ChatSourceRepository = Depends(ChatSourceRepository),
    ):
        self.session_repository = session_repository
        self.message_repository = message_repository
        self.source_repository = source_repository
        # Lazy initialization of VectorService - only created when needed
        self._vector_service = None
    
    def _get_vector_service(self) -> VectorService:
        """Lazy initialization of VectorService to avoid startup failures"""
        if self._vector_service is None:
            collection_name = settings.qdrant_collection_name if hasattr(settings, 'qdrant_collection_name') else "chat_documents"
            self._vector_service = VectorService(collection_name=collection_name)
        return self._vector_service

    async def send_message(
        self,
        session_id: UUID,
        user_id: UUID,
        data: SendMessageSchema,
    ) -> dict:
        """
        Send a message and get AI response with RAG context
        Returns both user message and assistant response
        """
        # Validate session exists and user owns it
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ResourceNotFoundException("Chat session not found")
        
        if session.user_id != user_id:
            raise UnauthorizedAccessException("You don't have permission to access this session")
        
        # Store user message
        user_message = await self.message_repository.create(
            session_id=session_id,
            role=MessageRole.USER,
            content=data.content,
            commit=True
        )
        
        # Query VectorService for relevant context
        # Search for documents related to user's message
        vector_service = self._get_vector_service()
        search_results = await vector_service.search(
            query=data.content,
            limit=5,
            user_id=str(user_id),
            session_id=str(session_id)
        )
        
        # Generate AI response (placeholder - integrate with LLM later)
        # For now, we'll create a simple response acknowledging the context
        context_summary = ""
        if search_results:
            context_summary = f"\n\nI found {len(search_results)} relevant document(s) that might help answer your question."
        
        assistant_content = f"I received your message: '{data.content}'{context_summary}\n\n[Note: LLM integration pending. This is a placeholder response.]"
        
        # Store assistant message
        assistant_message = await self.message_repository.create(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            commit=True
        )
        
        # Store source references for assistant message
        sources = []
        if search_results:
            source_data = [
                {
                    "message_id": assistant_message.id,
                    "source_type": result.get("metadata", {}).get("source_type", "document"),
                    "source_name": result.get("metadata", {}).get("filename", result.get("metadata", {}).get("source", "Unknown")),
                    "chunk_id": result.get("metadata", {}).get("chunk_id"),
                    "source_metadata": {
                        "score": result.get("score"),
                        "content_preview": result.get("content", "")[:200],  # First 200 chars
                        **result.get("metadata", {})
                    }
                }
                for result in search_results
            ]
            sources = await self.source_repository.create_bulk(source_data, commit=True)
        
        # Return both messages
        return {
            "user_message": ChatMessageWithSourcesSchema(
                id=user_message.id,
                session_id=user_message.session_id,
                role=user_message.role,
                content=user_message.content,
                created_at=user_message.created_at,
                sources=[]
            ),
            "assistant_message": ChatMessageWithSourcesSchema(
                id=assistant_message.id,
                session_id=assistant_message.session_id,
                role=assistant_message.role,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                sources=[ChatSourceResponseSchema.model_validate(source) for source in sources]
            )
        }

    async def get_conversation_history(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> ChatConversationResponseSchema:
        """Get full conversation history with sources"""
        # Validate session exists and user owns it
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ResourceNotFoundException("Chat session not found")
        
        if session.user_id != user_id:
            raise UnauthorizedAccessException("You don't have permission to access this session")
        
        # Get all messages with sources
        messages = await self.message_repository.get_session_messages_with_sources(session_id)
        
        # Convert to response schema
        message_schemas = [
            ChatMessageWithSourcesSchema(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                sources=[ChatSourceResponseSchema.model_validate(source) for source in msg.sources]
            )
            for msg in messages
        ]
        
        return ChatConversationResponseSchema(
            session_id=session_id,
            messages=message_schemas
        )


def get_chat_message_service(
    session_repository: ChatSessionRepository = Depends(ChatSessionRepository),
    message_repository: ChatMessageRepository = Depends(ChatMessageRepository),
    source_repository: ChatSourceRepository = Depends(ChatSourceRepository),
) -> ChatMessageService:
    """Dependency injection for ChatMessageService"""
    return ChatMessageService(session_repository, message_repository, source_repository)
