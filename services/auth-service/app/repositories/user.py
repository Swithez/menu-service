import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import Role, User


def _user_opts():
    """Standard eager-load options for User queries."""
    return selectinload(User.role).selectinload(Role.role_permissions)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Read ──────────────────────────────────────────────────────────────────

    async def list_all(self) -> Sequence[User]:
        result = await self._s.execute(
            select(User).options(_user_opts()).order_by(User.created_at)
        )
        return result.scalars().all()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._s.execute(
            select(User)
            .where(User.id == user_id)
            .options(_user_opts())
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._s.execute(
            select(User)
            .where(User.email == email)
            .options(_user_opts())
        )
        return result.scalar_one_or_none()

    async def exists_any(self) -> bool:
        result = await self._s.execute(select(User).limit(1))
        return result.scalar_one_or_none() is not None

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        email: str,
        full_name: str,
        hashed_password: str,
        role_id: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role_id=role_id,
            is_active=is_active,
        )
        self._s.add(user)
        await self._s.flush()
        # Re-fetch with eager loads
        return await self.get_by_id(user.id)  # type: ignore[return-value]

    async def update(
        self,
        user: User,
        full_name: str | None = None,
        role_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        hashed_password: str | None = None,
    ) -> User:
        if full_name is not None:
            user.full_name = full_name
        if role_id is not None:
            user.role_id = role_id
        if is_active is not None:
            user.is_active = is_active
        if hashed_password is not None:
            user.hashed_password = hashed_password
        await self._s.flush()
        # Re-fetch with eager loads to reflect role changes
        return await self.get_by_id(user.id)  # type: ignore[return-value]

    async def delete(self, user: User) -> None:
        await self._s.delete(user)
        await self._s.flush()
