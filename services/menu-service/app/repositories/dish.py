import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishIngredient, PriceHistory
from app.schemas.dish import DishCreate, DishIngredientCreate, DishUpdate


class DishRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: DishCreate) -> Dish:
        dish = Dish(**data.model_dump())
        self._session.add(dish)
        await self._session.flush()
        return await self.get_by_id(dish.id)  # type: ignore[return-value]

    async def get_by_id(self, dish_id: uuid.UUID) -> Dish | None:
        result = await self._session.execute(
            select(Dish)
            .options(selectinload(Dish.price_history), selectinload(Dish.ingredients))
            .where(Dish.id == dish_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        category_id: uuid.UUID | None = None,
        available_only: bool = False,
    ) -> list[Dish]:
        query = select(Dish).options(selectinload(Dish.price_history), selectinload(Dish.ingredients))
        if category_id is not None:
            query = query.where(Dish.category_id == category_id)
        if available_only:
            query = query.where(Dish.is_available.is_(True))
        query = query.order_by(Dish.name)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, dish: Dish, data: DishUpdate) -> Dish:
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(dish, field, value)
        await self._session.flush()
        return await self.get_by_id(dish.id)  # type: ignore[return-value]

    async def update_price(self, dish: Dish, new_price: Decimal) -> Dish:
        old_price = dish.price
        dish.price = new_price
        history = PriceHistory(dish_id=dish.id, old_price=old_price, new_price=new_price)
        self._session.add(history)
        await self._session.flush()
        return await self.get_by_id(dish.id)  # type: ignore[return-value]

    async def delete(self, dish: Dish) -> None:
        await self._session.delete(dish)
        await self._session.flush()

    async def get_price_history(self, dish_id: uuid.UUID) -> list[PriceHistory]:
        result = await self._session.execute(
            select(PriceHistory)
            .where(PriceHistory.dish_id == dish_id)
            .order_by(PriceHistory.changed_at.desc())
        )
        return list(result.scalars().all())

    async def get_ingredients(self, dish_id: uuid.UUID) -> list[DishIngredient]:
        result = await self._session.execute(
            select(DishIngredient)
            .where(DishIngredient.dish_id == dish_id)
            .order_by(DishIngredient.product_name)
        )
        return list(result.scalars().all())

    async def add_ingredient(self, dish_id: uuid.UUID, data: DishIngredientCreate) -> DishIngredient:
        ingredient = DishIngredient(dish_id=dish_id, **data.model_dump())
        self._session.add(ingredient)
        await self._session.flush()
        return ingredient

    async def delete_ingredient(self, ingredient_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(DishIngredient).where(DishIngredient.id == ingredient_id)
        )
        ingredient = result.scalar_one_or_none()
        if not ingredient:
            return False
        await self._session.delete(ingredient)
        await self._session.flush()
        return True
