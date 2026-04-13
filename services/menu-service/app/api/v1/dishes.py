import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.category import CategoryRepository
from app.repositories.dish import DishRepository
from app.schemas.dish import DishCreate, DishResponse, DishUpdate, PriceHistoryResponse, PriceUpdate
from app.services.dish import DishService

router = APIRouter(prefix="/dishes", tags=["dishes"])


def get_dish_service(session: Annotated[AsyncSession, Depends(get_db)]) -> DishService:
    return DishService(DishRepository(session), CategoryRepository(session))


@router.post("/", response_model=DishResponse, status_code=HTTPStatus.CREATED)
async def create_dish(
    data: DishCreate,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> DishResponse:
    dish = await service.create_dish(data)
    return DishResponse.model_validate(dish)


@router.get("/", response_model=list[DishResponse])
async def list_dishes(
    service: Annotated[DishService, Depends(get_dish_service)],
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    available_only: Annotated[bool, Query()] = False,
) -> list[DishResponse]:
    dishes = await service.list_dishes(category_id=category_id, available_only=available_only)
    return [DishResponse.model_validate(d) for d in dishes]


@router.get("/{dish_id}", response_model=DishResponse)
async def get_dish(
    dish_id: uuid.UUID,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> DishResponse:
    dish = await service.get_dish(dish_id)
    return DishResponse.model_validate(dish)


@router.patch("/{dish_id}", response_model=DishResponse)
async def update_dish(
    dish_id: uuid.UUID,
    data: DishUpdate,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> DishResponse:
    dish = await service.update_dish(dish_id, data)
    return DishResponse.model_validate(dish)


@router.patch("/{dish_id}/price", response_model=DishResponse)
async def update_price(
    dish_id: uuid.UUID,
    data: PriceUpdate,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> DishResponse:
    dish = await service.update_price(dish_id, data)
    return DishResponse.model_validate(dish)


@router.get("/{dish_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(
    dish_id: uuid.UUID,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> list[PriceHistoryResponse]:
    history = await service.get_price_history(dish_id)
    return [PriceHistoryResponse.model_validate(h) for h in history]


@router.delete("/{dish_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_dish(
    dish_id: uuid.UUID,
    service: Annotated[DishService, Depends(get_dish_service)],
) -> None:
    await service.delete_dish(dish_id)
