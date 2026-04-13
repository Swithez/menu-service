import uuid
from http import HTTPStatus

from fastapi import HTTPException

from app.models.product import Product, StockMovement
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjust


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def create_product(self, data: ProductCreate) -> Product:
        existing = await self._repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Product '{data.name}' already exists",
            )
        return await self._repo.create(data)

    async def get_product(self, product_id: uuid.UUID) -> Product:
        product = await self._repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return product

    async def list_products(self, *, low_stock_only: bool = False) -> list[Product]:
        return await self._repo.list_all(low_stock_only=low_stock_only)

    async def update_product(self, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = await self.get_product(product_id)
        if data.name is not None and data.name != product.name:
            existing = await self._repo.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"Product '{data.name}' already exists",
                )
        return await self._repo.update(product, data)

    async def adjust_stock(self, product_id: uuid.UUID, data: StockAdjust) -> tuple[Product, StockMovement]:
        product = await self.get_product(product_id)
        try:
            return await self._repo.adjust_stock(product, data)
        except ValueError as exc:
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc))

    async def get_movements(self, product_id: uuid.UUID) -> list[StockMovement]:
        await self.get_product(product_id)
        return await self._repo.get_movements(product_id)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        product = await self.get_product(product_id)
        await self._repo.delete(product)
