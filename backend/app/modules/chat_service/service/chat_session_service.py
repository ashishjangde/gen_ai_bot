from uuid import UUID
from fastapi import Depends
from app.modules.chat_service.repositories.chat_session_repository import ChatSessionRepository
from app.modules.chat_service.schema.chat_session_schema import (
    CreateChatSessionSchema,
    UpdateChatSessionSchema,
    ChatSessionResponseSchema,
    ChatSessionListResponseSchema,
)
from app.exceptions.exceptions import (
    ResourceNotFoundException,
    UnauthorizedAccessException,
)


class ChatSessionService:
    """Service for managing chat sessions"""
    
    def __init__(
        self,
        session_repository: ChatSessionRepository = Depends(ChatSessionRepository),
    ):
        self.session_repository = session_repository

    async def create_session(
        self, 
        user_id: UUID, 
        data: CreateChatSessionSchema
    ) -> ChatSessionResponseSchema:
        """Create a new chat session for a user"""
        session = await self.session_repository.create(
            user_id=user_id,
            title=data.title,
            commit=True
        )
        return ChatSessionResponseSchema.model_validate(session)

    async def get_user_sessions(
        self, 
        user_id: UUID
    ) -> list[ChatSessionListResponseSchema]:
        """Get all chat sessions for a user with message counts"""
        sessions_with_counts = await self.session_repository.get_sessions_with_message_count(user_id)
        
        return [
            ChatSessionListResponseSchema(
                id=item["session"].id,
                user_id=item["session"].user_id,
                title=item["session"].title,
                created_at=item["session"].created_at,
                updated_at=item["session"].updated_at,
                message_count=item["message_count"]
            )
            for item in sessions_with_counts
        ]

    async def get_session(
        self, 
        session_id: UUID, 
        user_id: UUID
    ) -> ChatSessionResponseSchema:
        """Get session details with user ownership validation"""
        session = await self.session_repository.get_by_id(session_id)
        
        if not session:
            raise ResourceNotFoundException("Chat session not found")
        
        if session.user_id != user_id:
            raise UnauthorizedAccessException("You don't have permission to access this session")
        
        return ChatSessionResponseSchema.model_validate(session)

    async def update_session(
        self, 
        session_id: UUID, 
        user_id: UUID, 
        data: UpdateChatSessionSchema
    ) -> ChatSessionResponseSchema:
        """Update session title with user ownership validation"""
        session = await self.session_repository.get_by_id(session_id)
        
        if not session:
            raise ResourceNotFoundException("Chat session not found")
        
        if session.user_id != user_id:
            raise UnauthorizedAccessException("You don't have permission to update this session")
        
        updated_session = await self.session_repository.update(
            id=session_id,
            title=data.title,
            commit=True
        )
        
        return ChatSessionResponseSchema.model_validate(updated_session)

    async def delete_session(
        self, 
        session_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete session with user ownership validation"""
        session = await self.session_repository.get_by_id(session_id)
        
        if not session:
            raise ResourceNotFoundException("Chat session not found")
        
        if session.user_id != user_id:
            raise UnauthorizedAccessException("You don't have permission to delete this session")
        
        return await self.session_repository.delete(id=session_id, commit=True)


def get_chat_session_service(
    session_repository: ChatSessionRepository = Depends(ChatSessionRepository),
) -> ChatSessionService:
    """Dependency injection for ChatSessionService"""
    return ChatSessionService(session_repository)
