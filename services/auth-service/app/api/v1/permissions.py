from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.permissions import ALL_PERMISSIONS, PERMISSION_GROUPS
from app.schemas.auth import PermissionSchema

router = APIRouter(prefix="/permissions", tags=["permissions"])

_can_read = Depends(require_permission("users:roles:manage"))


@router.get(
    "",
    response_model=list[PermissionSchema],
    summary="List all available permissions",
    dependencies=[_can_read],
)
async def list_permissions():
    return [
        PermissionSchema(code=p.code, description=p.description, group=p.group)
        for p in ALL_PERMISSIONS
    ]


@router.get(
    "/groups",
    response_model=dict[str, list[PermissionSchema]],
    summary="Permissions grouped by domain",
    dependencies=[_can_read],
)
async def list_permissions_grouped():
    return {
        group: [
            PermissionSchema(code=p.code, description=p.description, group=p.group)
            for p in perms
        ]
        for group, perms in PERMISSION_GROUPS.items()
    }
