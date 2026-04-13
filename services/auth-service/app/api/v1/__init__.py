from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.permissions import router as permissions_router
from app.api.v1.roles import router as roles_router
from app.api.v1.users import router as users_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(permissions_router)
v1_router.include_router(roles_router)
v1_router.include_router(users_router)
