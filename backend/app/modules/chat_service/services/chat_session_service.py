from uuid import UUID
from fastapi import Depends
from app.modules.chat_service.repositories.chat_sessions_repository import ChatSessionRepository
from app.modules.chat_service.repositories.chat_repository import ChatMessageRepository
from app.modules.chat_service.schema.chat_session_schema import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionSchema, ChatSessionWithMessagesSchema
)
from app.modules.chat_service.schema.chat_schema import ChatMessageSchema
from app.modules.chat_service.services.memory_service import ShortTermMemory
from app.exceptions.exceptions import ResourceNotFoundException


class ChatSessionService:
    """Service for managing chat sessions"""
    
    def __init__(
        self,
        session_repo: ChatSessionRepository,
        message_repo: ChatMessageRepository,
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo
    
    async def create_session(
        self, user_id: UUID, data: ChatSessionCreate
    ) -> ChatSessionSchema:
        """Create a new chat session"""
        session = await self.session_repo.create(
            user_id=user_id,
            title=data.title or "New Chat",
            commit=True,
        )
        return ChatSessionSchema.model_validate(session)
    
    async def get_sessions(self, user_id: UUID) -> list[ChatSessionSchema]:
        """Get all sessions for a user"""
        sessions = await self.session_repo.get_by_user_id(user_id)
        return [ChatSessionSchema.model_validate(s) for s in sessions]
    
    async def get_session(
        self, session_id: UUID, user_id: UUID
    ) -> ChatSessionWithMessagesSchema:
        """Get a session with messages"""
        session = await self.session_repo.get_with_messages(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        return ChatSessionWithMessagesSchema.model_validate(session)
    
    async def get_session_messages(
        self, session_id: UUID, user_id: UUID
    ) -> list[ChatMessageSchema]:
        """Get all messages for a session"""
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        messages = await self.message_repo.get_by_session_id(session_id)
        return [ChatMessageSchema.model_validate(m) for m in messages]
    
    async def update_session(
        self, session_id: UUID, user_id: UUID, data: ChatSessionUpdate
    ) -> ChatSessionSchema:
        """Update a session"""
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        update_data = {}
        if data.title is not None:
            update_data["title"] = data.title
        
        if update_data:
            session = await self.session_repo.update(
                id=session_id, commit=True, **update_data
            )
        
        return ChatSessionSchema.model_validate(session)
    
    async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """Delete a session and clear its STM"""
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        # Clear short-term memory
        await ShortTermMemory.clear_session(session_id)
        
        # Delete from DB (cascades to messages and sources)
        await self.session_repo.delete(id=session_id, commit=True)
        return True


def get_chat_session_service(
    session_repo: ChatSessionRepository = Depends(ChatSessionRepository),
    message_repo: ChatMessageRepository = Depends(ChatMessageRepository),
) -> ChatSessionService:
    return ChatSessionService(session_repo, message_repo)
