from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession , create_async_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL="postgresql+asyncpg://system:manager@localhost:5432/gen_ai"

engine = create_async_engine(url=DATABASE_URL , echo=True)

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