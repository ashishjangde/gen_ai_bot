"""
User repository for database operations.
"""

from uuid import UUID
from sqlalchemy import select
from mvp.app.config.base_repository import BaseRepository
from mvp.app.models.user_model import User


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_active_by_id(self, user_id: UUID) -> User | None:
        """Get active user by ID."""
        stmt = select(self.model).where(
            self.model.id == user_id,
            self.model.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
