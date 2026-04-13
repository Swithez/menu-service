import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, require_permission
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

_manage_users = Depends(require_permission("users:users:manage"))


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users",
    dependencies=[_manage_users],
)
async def list_users(session: SessionDep):
    return await UserService(session).list_users()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    dependencies=[_manage_users],
)
async def create_user(body: UserCreate, session: SessionDep):
    try:
        return await UserService(session).create_user(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a single user",
    dependencies=[_manage_users],
)
async def get_user(user_id: uuid.UUID, session: SessionDep):
    try:
        return await UserService(session).get_user(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    dependencies=[_manage_users],
)
async def update_user(user_id: uuid.UUID, body: UserUpdate, session: SessionDep):
    try:
        return await UserService(session).update_user(user_id, body)
    except ValueError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=str(exc))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    dependencies=[_manage_users],
)
async def delete_user(user_id: uuid.UUID, session: SessionDep):
    try:
        await UserService(session).delete_user(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
