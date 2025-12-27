from typing import Any
from sqlalchemy import delete, select
from app.config.base_repository import BaseRepository
from app.modules.user_service.models.session_model import Session


class SessionRepository(BaseRepository[Session]):
    model = Session

    async def get_by_refresh_token(self, refresh_token: str) -> Session | None:
        stmt = select(self.model).where(self.model.refresh_token == refresh_token)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_user_id(self, user_id: Any) -> list[Session]:
        stmt = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_user_id(self, user_id: Any) -> None:
        stmt = delete(self.model).where(self.model.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_by_refresh_token(self, refresh_token: str) -> None:
        stmt = delete(self.model).where(self.model.refresh_token == refresh_token)
        await self.session.execute(stmt)
        await self.session.commit()

    async def enforce_session_limit(self, user_id: Any, limit: int = 3) -> None:
        stmt = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.asc())
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()
        
        if len(sessions) >= limit:
            sessions_to_delete = sessions[:(len(sessions) - limit + 1)]
            for session in sessions_to_delete:
                await self.session.delete(session)
            await self.session.commit()

