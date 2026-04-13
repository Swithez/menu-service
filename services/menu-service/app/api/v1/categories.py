import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_service(session: Annotated[AsyncSession, Depends(get_db)]) -> CategoryService:
    return CategoryService(CategoryRepository(session))


@router.post("/", response_model=CategoryResponse, status_code=HTTPStatus.CREATED)
async def create_category(
    data: CategoryCreate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.create_category(data)
    return CategoryResponse.model_validate(category)


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
    active_only: Annotated[bool, Query(description="Return only active categories")] = False,
) -> list[CategoryResponse]:
    categories = await service.list_categories(active_only=active_only)
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.get_category(category_id)
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    category = await service.update_category(category_id, data)
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> None:
    await service.delete_category(category_id)
