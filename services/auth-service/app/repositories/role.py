import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import Permission, Role, RolePermission


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Read ──────────────────────────────────────────────────────────────────

    async def list_all(self) -> Sequence[Role]:
        result = await self._s.execute(
            select(Role)
            .order_by(Role.name)
            .options(selectinload(Role.role_permissions))
        )
        return result.scalars().all()

    async def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self._s.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.role_permissions))
            # populate_existing forces refresh of identity-map objects
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._s.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(self, name: str, description: str | None = None) -> Role:
        role = Role(name=name, description=description)
        self._s.add(role)
        await self._s.flush()
        return role

    async def update(
        self,
        role: Role,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        await self._s.flush()
        return role

    async def delete(self, role: Role) -> None:
        await self._s.delete(role)
        await self._s.flush()

    # ── Permissions ───────────────────────────────────────────────────────────

    async def set_permissions(
        self, role_id: uuid.UUID, permission_codes: list[str]
    ) -> None:
        """Replace all permissions for a role atomically."""
        await self._s.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for code in permission_codes:
            self._s.add(RolePermission(role_id=role_id, permission_code=code))
        await self._s.flush()

    async def count_users(self, role_id: uuid.UUID) -> int:
        from app.models.auth import User
        result = await self._s.execute(
            select(User).where(User.role_id == role_id)
        )
        return len(result.scalars().all())
