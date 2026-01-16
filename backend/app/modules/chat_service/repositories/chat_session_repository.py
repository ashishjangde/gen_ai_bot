from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.config.base_repository import BaseRepository
from app.modules.chat_service.models.chat_sessions import ChatSessions


class ChatSessionRepository(BaseRepository[ChatSessions]):
    """Repository for chat session operations"""
    model = ChatSessions

    async def get_by_user_id(self, user_id: UUID) -> list[ChatSessions]:
        """Get all chat sessions for a user, ordered by most recent"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_session_with_messages(self, session_id: UUID) -> ChatSessions | None:
        """Get session with messages eagerly loaded"""
        stmt = (
            select(self.model)
            .where(self.model.id == session_id)
            .options(selectinload(self.model.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_sessions_with_message_count(self, user_id: UUID) -> list[dict]:
        """Get all sessions for a user with message counts"""
        from app.modules.chat_service.models.chat_session_messages import ChatSessionMessages
        
        stmt = (
            select(
                self.model,
                func.count(ChatSessionMessages.id).label("message_count")
            )
            .outerjoin(ChatSessionMessages, self.model.id == ChatSessionMessages.session_id)
            .where(self.model.user_id == user_id)
            .group_by(self.model.id)
            .order_by(self.model.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        
        sessions_with_counts = []
        for row in result:
            session = row[0]
            message_count = row[1] or 0
            sessions_with_counts.append({
                "session": session,
                "message_count": message_count
            })
        
        return sessions_with_counts
