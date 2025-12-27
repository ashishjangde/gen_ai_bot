from sqlalchemy import select
from app.config.base_repository import BaseRepository
from app.modules.user_service.models.user_model import User

class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
   
    