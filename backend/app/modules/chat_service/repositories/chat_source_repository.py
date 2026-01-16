from uuid import UUID
from sqlalchemy import select
from app.config.base_repository import BaseRepository
from app.modules.chat_service.models.chat_session_sources import ChatMessageSource


class ChatSourceRepository(BaseRepository[ChatMessageSource]):
    """Repository for chat message source operations"""
    model = ChatMessageSource

    async def get_by_message_id(self, message_id: UUID) -> list[ChatMessageSource]:
        """Get all sources for a message"""
        stmt = (
            select(self.model)
            .where(self.model.message_id == message_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_bulk(self, sources: list[dict], commit: bool = True) -> list[ChatMessageSource]:
        """Create multiple source records efficiently"""
        source_objects = [self.model(**source_data) for source_data in sources]
        self.session.add_all(source_objects)
        
        if commit:
            await self.session.commit()
            for obj in source_objects:
                await self.session.refresh(obj)
        
        return source_objects
