import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import Role
from app.permissions import PERMISSION_MAP
from app.repositories.role import RoleRepository
from app.schemas.auth import PermissionSchema, RoleCreate, RoleDetailResponse, RoleResponse, RoleUpdate


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = RoleRepository(session)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _permission_schemas(role: Role) -> list[PermissionSchema]:
        """Build PermissionSchema list from role_permissions + PERMISSION_MAP."""
        result = []
        for rp in role.role_permissions:
            p = PERMISSION_MAP.get(rp.permission_code)
            if p:
                result.append(
                    PermissionSchema(code=p.code, description=p.description, group=p.group)
                )
        return sorted(result, key=lambda x: (x.group, x.code))

    @staticmethod
    def _to_response(role: Role) -> RoleResponse:
        perm_count = len(role.role_permissions)
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            permission_count=perm_count,
        )

    @classmethod
    def _to_detail(cls, role: Role) -> RoleDetailResponse:
        perms = cls._permission_schemas(role)
        return RoleDetailResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            created_at=role.created_at,
            permission_count=len(perms),
            permissions=perms,
        )

    # ── Queries ───────────────────────────────────────────────────────────────

    async def list_roles(self) -> list[RoleResponse]:
        roles = await self._repo.list_all()
        return [self._to_response(r) for r in roles]

    async def get_role(self, role_id: uuid.UUID) -> RoleDetailResponse:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")
        return self._to_detail(role)

    # ── Commands ──────────────────────────────────────────────────────────────

    async def create_role(self, data: RoleCreate) -> RoleDetailResponse:
        if await self._repo.get_by_name(data.name):
            raise ValueError(f"Role '{data.name}' already exists")

        invalid = [c for c in data.permission_codes if c not in PERMISSION_MAP]
        if invalid:
            raise ValueError(f"Unknown permission codes: {invalid}")

        role = await self._repo.create(name=data.name, description=data.description)
        if data.permission_codes:
            await self._repo.set_permissions(role.id, data.permission_codes)

        role = await self._repo.get_by_id(role.id)
        return self._to_detail(role)  # type: ignore[arg-type]

    async def update_role(
        self, role_id: uuid.UUID, data: RoleUpdate
    ) -> RoleDetailResponse:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")

        if data.name and data.name != role.name:
            if await self._repo.get_by_name(data.name):
                raise ValueError(f"Role '{data.name}' already exists")

        await self._repo.update(role, name=data.name, description=data.description)
        role = await self._repo.get_by_id(role_id)
        return self._to_detail(role)  # type: ignore[arg-type]

    async def set_permissions(
        self, role_id: uuid.UUID, permission_codes: list[str]
    ) -> RoleDetailResponse:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")

        invalid = [c for c in permission_codes if c not in PERMISSION_MAP]
        if invalid:
            raise ValueError(f"Unknown permission codes: {invalid}")

        await self._repo.set_permissions(role_id, permission_codes)
        role = await self._repo.get_by_id(role_id)
        return self._to_detail(role)  # type: ignore[arg-type]

    async def delete_role(self, role_id: uuid.UUID) -> None:
        role = await self._repo.get_by_id(role_id)
        if role is None:
            raise ValueError(f"Role {role_id} not found")
        if role.is_system:
            raise ValueError("Cannot delete a system role")
        count = await self._repo.count_users(role_id)
        if count > 0:
            raise ValueError(f"Role is assigned to {count} user(s). Reassign first.")
        await self._repo.delete(role)
