from uuid import UUID
from sqlalchemy import select
from app.config.base_repository import BaseRepository
from app.modules.chat_service.models.chat_session_model import ChatSession


class ChatSessionRepository(BaseRepository[ChatSession]):
    model = ChatSession

    async def get_by_user_id(self, user_id: UUID) -> list[ChatSession]:
        """Get all sessions for a user, ordered by updated_at desc"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(self, session_id: UUID) -> ChatSession | None:
        """Get session with messages loaded"""
        stmt = select(self.model).where(self.model.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
