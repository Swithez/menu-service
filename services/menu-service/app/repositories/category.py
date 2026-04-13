import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CategoryCreate) -> Category:
        category = Category(**data.model_dump())
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self._session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, active_only: bool = False) -> list[Category]:
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active.is_(True))
        query = query.order_by(Category.name)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()
