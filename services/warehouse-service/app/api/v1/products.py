import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockAdjust,
    StockMovementResponse,
)
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ProductService:
    return ProductService(ProductRepository(session))


@router.post("/", response_model=ProductResponse, status_code=HTTPStatus.CREATED)
async def create_product(
    data: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.create_product(data)
    return ProductResponse.model_validate(product)


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    low_stock_only: Annotated[bool, Query(description="Show only products below minimum stock")] = False,
) -> list[ProductResponse]:
    products = await service.list_products(low_stock_only=low_stock_only)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.get_product(product_id)
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await service.update_product(product_id, data)
    return ProductResponse.model_validate(product)


@router.post("/{product_id}/stock", response_model=ProductResponse)
async def adjust_stock(
    product_id: uuid.UUID,
    data: StockAdjust,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product, _ = await service.adjust_stock(product_id, data)
    return ProductResponse.model_validate(product)


@router.get("/{product_id}/movements", response_model=list[StockMovementResponse])
async def get_movements(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> list[StockMovementResponse]:
    movements = await service.get_movements(product_id)
    return [StockMovementResponse.model_validate(m) for m in movements]


@router.delete("/{product_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    await service.delete_product(product_id)
