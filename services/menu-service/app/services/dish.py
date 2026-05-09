import uuid
from http import HTTPStatus

from fastapi import HTTPException

from app.models.dish import Dish, DishIngredient, PriceHistory
from app.repositories.category import CategoryRepository
from app.repositories.dish import DishRepository
from app.schemas.dish import DishCreate, DishIngredientCreate, DishUpdate, PriceUpdate


class DishService:
    def __init__(self, dish_repo: DishRepository, category_repo: CategoryRepository) -> None:
        self._dish_repo = dish_repo
        self._category_repo = category_repo

    async def create_dish(self, data: DishCreate) -> Dish:
        if data.category_id is not None:
            category = await self._category_repo.get_by_id(data.category_id)
            if not category:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Category {data.category_id} not found",
                )
        return await self._dish_repo.create(data)

    async def get_dish(self, dish_id: uuid.UUID) -> Dish:
        dish = await self._dish_repo.get_by_id(dish_id)
        if not dish:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Dish {dish_id} not found",
            )
        return dish

    async def list_dishes(
        self,
        *,
        category_id: uuid.UUID | None = None,
        available_only: bool = False,
    ) -> list[Dish]:
        return await self._dish_repo.list_all(
            category_id=category_id, available_only=available_only
        )

    async def update_dish(self, dish_id: uuid.UUID, data: DishUpdate) -> Dish:
        dish = await self.get_dish(dish_id)
        if data.category_id is not None:
            category = await self._category_repo.get_by_id(data.category_id)
            if not category:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Category {data.category_id} not found",
                )
        return await self._dish_repo.update(dish, data)

    async def update_price(self, dish_id: uuid.UUID, data: PriceUpdate) -> Dish:
        dish = await self.get_dish(dish_id)
        if dish.price == data.price:
            return dish
        return await self._dish_repo.update_price(dish, data.price)

    async def delete_dish(self, dish_id: uuid.UUID) -> None:
        dish = await self.get_dish(dish_id)
        await self._dish_repo.delete(dish)

    async def get_price_history(self, dish_id: uuid.UUID) -> list[PriceHistory]:
        await self.get_dish(dish_id)
        return await self._dish_repo.get_price_history(dish_id)

    async def get_ingredients(self, dish_id: uuid.UUID) -> list[DishIngredient]:
        await self.get_dish(dish_id)
        return await self._dish_repo.get_ingredients(dish_id)

    async def add_ingredient(self, dish_id: uuid.UUID, data: DishIngredientCreate) -> DishIngredient:
        await self.get_dish(dish_id)
        return await self._dish_repo.add_ingredient(dish_id, data)

    async def delete_ingredient(self, dish_id: uuid.UUID, ingredient_id: uuid.UUID) -> None:
        await self.get_dish(dish_id)
        deleted = await self._dish_repo.delete_ingredient(ingredient_id)
        if not deleted:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Ingredient {ingredient_id} not found",
            )
