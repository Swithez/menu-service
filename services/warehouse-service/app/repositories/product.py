import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import MovementType, Product, StockMovement
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjust


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ProductCreate) -> Product:
        product = Product(
            name=data.name,
            unit=data.unit,
            calories_per_unit=data.calories_per_unit,
            min_stock_level=data.min_stock_level,
            cost_price=data.cost_price,
            current_stock=data.initial_stock,
        )
        self._session.add(product)
        await self._session.flush()
        if data.initial_stock > 0:
            movement = StockMovement(
                product_id=product.id,
                quantity=data.initial_stock,
                movement_type=MovementType.INCOMING,
                reason="Initial stock",
            )
            self._session.add(movement)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self._session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Product | None:
        result = await self._session.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, low_stock_only: bool = False) -> list[Product]:
        query = select(Product).order_by(Product.name)
        result = await self._session.execute(query)
        products = list(result.scalars().all())
        if low_stock_only:
            products = [p for p in products if p.is_low_stock]
        return products

    async def update(self, product: Product, data: ProductUpdate) -> Product:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def adjust_stock(self, product: Product, data: StockAdjust) -> tuple[Product, StockMovement]:
        effective_qty = data.quantity if data.movement_type == MovementType.INCOMING else -abs(data.quantity)
        new_stock = product.current_stock + effective_qty
        if new_stock < 0:
            raise ValueError(
                f"Insufficient stock: {product.current_stock} {product.unit} available, "
                f"requested {abs(data.quantity)}"
            )
        product.current_stock = new_stock
        movement = StockMovement(
            product_id=product.id,
            quantity=data.quantity,
            movement_type=data.movement_type,
            reason=data.reason,
            order_id=data.order_id,
        )
        self._session.add(movement)
        await self._session.flush()
        await self._session.refresh(product)
        return product, movement

    async def get_movements(self, product_id: uuid.UUID) -> list[StockMovement]:
        result = await self._session.execute(
            select(StockMovement)
            .where(StockMovement.product_id == product_id)
            .order_by(StockMovement.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, product: Product) -> None:
        await self._session.delete(product)
        await self._session.flush()
