from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.config.base_repository import BaseRepository
from app.modules.chat_service.models.chat_session_messages import ChatSessionMessages


class ChatMessageRepository(BaseRepository[ChatSessionMessages]):
    """Repository for chat message operations"""
    model = ChatSessionMessages

    async def get_by_session_id(self, session_id: UUID) -> list[ChatSessionMessages]:
        """Get all messages for a session, ordered by creation time"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_message_with_sources(self, message_id: UUID) -> ChatSessionMessages | None:
        """Get message with source references eagerly loaded"""
        stmt = (
            select(self.model)
            .where(self.model.id == message_id)
            .options(selectinload(self.model.sources))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_session_messages_with_sources(self, session_id: UUID) -> list[ChatSessionMessages]:
        """Get all messages for a session with sources eagerly loaded"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .options(selectinload(self.model.sources))
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
