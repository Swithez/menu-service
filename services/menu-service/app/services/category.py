import uuid
from http import HTTPStatus

from fastapi import HTTPException

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def create_category(self, data: CategoryCreate) -> Category:
        existing = await self._repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Category with name '{data.name}' already exists",
            )
        return await self._repo.create(data)

    async def get_category(self, category_id: uuid.UUID) -> Category:
        category = await self._repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        return category

    async def list_categories(self, *, active_only: bool = False) -> list[Category]:
        return await self._repo.list_all(active_only=active_only)

    async def update_category(self, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
        category = await self.get_category(category_id)
        if data.name is not None and data.name != category.name:
            existing = await self._repo.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"Category with name '{data.name}' already exists",
                )
        return await self._repo.update(category, data)

    async def delete_category(self, category_id: uuid.UUID) -> None:
        category = await self.get_category(category_id)
        await self._repo.delete(category)
