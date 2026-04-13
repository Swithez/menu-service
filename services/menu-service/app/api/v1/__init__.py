from fastapi import APIRouter

from app.api.v1.categories import router as categories_router
from app.api.v1.dishes import router as dishes_router

router = APIRouter(prefix="/api/v1")
router.include_router(categories_router)
router.include_router(dishes_router)
