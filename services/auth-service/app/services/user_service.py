import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import hash_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # ── Queries ───────────────────────────────────────────────────────────────

    async def list_users(self) -> list[UserResponse]:
        users = await self._repo.list_all()
        return [self._to_response(u) for u in users]

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return self._to_response(user)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def create_user(self, data: UserCreate) -> UserResponse:
        if await self._repo.get_by_email(data.email):
            raise ValueError(f"Email '{data.email}' already registered")
        user = await self._repo.create(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role_id=data.role_id,
            is_active=data.is_active,
        )
        return self._to_response(user)

    async def update_user(
        self, user_id: uuid.UUID, data: UserUpdate
    ) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        hashed: str | None = None
        if data.password is not None:
            hashed = hash_password(data.password)

        user = await self._repo.update(
            user,
            full_name=data.full_name,
            role_id=data.role_id,
            is_active=data.is_active,
            hashed_password=hashed,
        )
        return self._to_response(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        await self._repo.delete(user)
