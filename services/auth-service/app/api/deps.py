from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.auth_service import decode_token

_bearer = HTTPBearer()


async def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    """Decode JWT; return payload dict or raise 401."""
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def require_permission(code: str):
    """FastAPI dependency factory: check that the caller has a specific permission."""

    async def _check(
        payload: Annotated[dict, Depends(get_current_user_payload)],
    ) -> dict:
        if code not in payload.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {code}",
            )
        return payload

    return _check


# Convenience aliases
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[dict, Depends(get_current_user_payload)]
