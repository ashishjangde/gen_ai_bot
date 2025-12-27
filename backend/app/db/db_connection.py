from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession , create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

engine = create_async_engine(url=settings.database_url , echo=settings.debug)

AsyncSessionLocal = sessionmaker(engine , class_=AsyncSession , expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()