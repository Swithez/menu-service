from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.api.v1 import v1_router
from app.config import settings
from app.database import Base, engine, get_session
from app.models.auth import Permission, Role, RolePermission, User
from app.permissions import ADMIN_PERMISSIONS, ALL_PERMISSIONS
from app.services.auth_service import hash_password


async def _seed(session):
    """Idempotent seed: permissions → admin role → admin user."""

    # 1. Upsert permissions
    for p in ALL_PERMISSIONS:
        existing = await session.get(Permission, p.code)
        if existing is None:
            session.add(Permission(code=p.code, description=p.description, group=p.group))
    await session.flush()

    # 2. Ensure admin role exists
    result = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    if admin_role is None:
        admin_role = Role(name="admin", description="Полный доступ", is_system=True)
        session.add(admin_role)
        await session.flush()

    # 3. Ensure admin role has all permissions
    existing_codes_result = await session.execute(
        select(RolePermission.permission_code).where(
            RolePermission.role_id == admin_role.id
        )
    )
    existing_codes = set(existing_codes_result.scalars().all())
    for code in ADMIN_PERMISSIONS:
        if code not in existing_codes:
            session.add(RolePermission(role_id=admin_role.id, permission_code=code))
    await session.flush()

    # 4. Ensure at least one admin user
    result = await session.execute(select(User).limit(1))
    if result.scalar_one_or_none() is None:
        session.add(
            User(
                email=settings.admin_email,
                full_name=settings.admin_full_name,
                hashed_password=hash_password(settings.admin_password),
                role_id=admin_role.id,
                is_active=True,
            )
        )
        await session.flush()

    await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_session():
        await _seed(session)
        break

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(v1_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
