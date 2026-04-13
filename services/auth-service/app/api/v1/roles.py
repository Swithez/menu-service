import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, require_permission
from app.schemas.auth import RoleCreate, RoleDetailResponse, RoleResponse, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])

_manage = Depends(require_permission("users:roles:manage"))


@router.get(
    "",
    response_model=list[RoleResponse],
    summary="List all roles",
    dependencies=[_manage],
)
async def list_roles(session: SessionDep):
    return await RoleService(session).list_roles()


@router.post(
    "",
    response_model=RoleDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    dependencies=[_manage],
)
async def create_role(body: RoleCreate, session: SessionDep):
    try:
        return await RoleService(session).create_role(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/{role_id}",
    response_model=RoleDetailResponse,
    summary="Get role with its permissions",
    dependencies=[_manage],
)
async def get_role(role_id: uuid.UUID, session: SessionDep):
    try:
        return await RoleService(session).get_role(role_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{role_id}",
    response_model=RoleDetailResponse,
    summary="Update role name / description",
    dependencies=[_manage],
)
async def update_role(role_id: uuid.UUID, body: RoleUpdate, session: SessionDep):
    try:
        return await RoleService(session).update_role(role_id, body)
    except ValueError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=str(exc))


@router.put(
    "/{role_id}/permissions",
    response_model=RoleDetailResponse,
    summary="Replace all permissions of a role",
    dependencies=[_manage],
)
async def set_permissions(
    role_id: uuid.UUID, body: list[str], session: SessionDep
):
    try:
        return await RoleService(session).set_permissions(role_id, body)
    except ValueError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(exc))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role (must not be system or have users)",
    dependencies=[_manage],
)
async def delete_role(role_id: uuid.UUID, session: SessionDep):
    try:
        await RoleService(session).delete_role(role_id)
    except ValueError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=str(exc))
