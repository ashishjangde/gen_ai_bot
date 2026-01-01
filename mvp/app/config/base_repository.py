from abc import ABC
from collections.abc import Sequence
from typing import Any, TypeVar
from fastapi import Depends
from sqlalchemy import Row, RowMapping, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from mvp.app.db.database import get_async_session

T = TypeVar("T", bound=DeclarativeBase)


class BaseRepository[T](ABC):
    """
    Base repository class for CRUD operations.
    This class provides a generic interface for database operations.
    """
    model: type[T]  # Child class must set this

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def create(self, commit: bool = True, **kwargs) -> T:
        data = self.model(**kwargs)
        self.session.add(data)
        if commit:
            await self.session.commit()
            await self.session.refresh(data)
        return data

    async def get_by_id(self, id: Any) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all_paginated(
        self, 
        offset: int = 0, 
        limit: int = 10, 
        query: str = "",
        order_by: str | None = None,
        descending: bool = True
    ) -> dict[str, Any]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if query:
            filters = []
            for column in self.model.__table__.columns:
                if (
                    hasattr(column.type, "python_type")
                    and column.type.python_type is str
                ):
                    filters.append(column.ilike(f"%{query}%"))
            if filters:
                stmt = stmt.where(or_(*filters))
                count_stmt = count_stmt.where(or_(*filters))

        # Apply ordering if specified
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            stmt = stmt.order_by(column.desc() if descending else column.asc())

        total_query = await self.session.execute(count_stmt)
        total = total_query.scalar_one()

        items_query = await self.session.execute(stmt.offset(offset).limit(limit))
        items = items_query.scalars().all()

        total_pages = (total // limit) + (1 if total % limit > 0 else 0)

        return {
            "total": total,
            self.model.__name__: items,
            "current_page": (offset // limit) + 1,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def get_all(self) -> Sequence[Row[Any] | RowMapping | Any]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_field(self, field: str, value: Any) -> T | None:
        if not hasattr(self.model, field):
            raise AttributeError(f"{self.model.__name__} has no attribute '{field}'")
        stmt = select(self.model).where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, id: Any, commit: bool = True, **kwargs) -> T | None:
        record = await self.get_by_id(id)
        if not record:
            return None
        for key, value in kwargs.items():
            setattr(record, key, value)
        if commit:
            await self.session.commit()
            await self.session.refresh(record)
        return record

    async def delete(self, id: Any, commit: bool = True) -> bool:
        record = await self.get_by_id(id)
        if record:
            await self.session.execute(delete(self.model).where(self.model.id == id))
            if commit:
                await self.session.commit()
            return True
        return False

    async def commit(self) -> None:
        """Manually commit the session (use after batch operations)."""
        await self.session.commit()