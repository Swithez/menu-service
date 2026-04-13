from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.models.auth import User


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user: User) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    expires_in = settings.access_token_expire_minutes * 60
    exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    permissions: list[str] = []
    if user.role and user.role.role_permissions:
        permissions = [rp.permission_code for rp in user.role.role_permissions]

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role_id": str(user.role_id) if user.role_id else None,
        "role_name": user.role.name if user.role else None,
        "permissions": permissions,
        "exp": exp,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_token(token: str) -> dict:
    """Decode and validate JWT; raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
