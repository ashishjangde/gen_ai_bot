from uuid import UUID
from sqlalchemy import select
from mvp.app.config.base_repository import BaseRepository
from mvp.app.models.chat_source_model import ChatSource


class ChatSourceRepository(BaseRepository[ChatSource]):
    model = ChatSource

    async def get_by_session_id(self, session_id: UUID) -> list[ChatSource]:
        """Get all sources for a session"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ready_sources(self, session_id: UUID) -> list[ChatSource]:
        """Get all ready sources for a session (for RAG queries)"""
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .where(self.model.status == "ready")
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id(self, user_id: UUID) -> list[ChatSource]:
        """Get all sources for a user"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
