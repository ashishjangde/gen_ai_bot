from uuid import UUID
from sqlalchemy import select
from app.config.base_repository import BaseRepository
from app.modules.chat_service.models.chat_model import ChatMessage


class ChatMessageRepository(BaseRepository[ChatMessage]):
    model = ChatMessage

    async def get_by_session_id(self, session_id: UUID) -> list[ChatMessage]:
        """Get all messages for a session, ordered by created_at asc"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, session_id: UUID, limit: int = 10) -> list[ChatMessage]:
        """Get most recent messages for a session"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
