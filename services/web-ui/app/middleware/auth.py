"""
JWT-based auth middleware for web-ui.

The JWT token is stored in the Flask session after login.
We decode it locally (same secret as auth-service) to avoid an extra
HTTP round-trip on every request.
"""
import functools
from datetime import datetime, timezone

from flask import abort, flash, g, redirect, request, session, url_for
from jose import JWTError, jwt

from app.config import settings

# Public paths that do NOT require authentication
_PUBLIC_PREFIXES = ("/auth/",)
_PUBLIC_EXACT = {"/health"}


def init_auth(app):
    """Register before_request hook on the Flask app."""

    @app.before_request
    def _check_auth():
        # Always allow static files
        if request.path.startswith("/static/"):
            return None

        # Always allow login/logout
        if any(request.path.startswith(p) for p in _PUBLIC_PREFIXES):
            return None
        if request.path in _PUBLIC_EXACT:
            return None

        token = session.get("access_token")
        if not token:
            flash("Войдите в систему", "warning")
            return redirect(url_for("auth.login", next=request.path))

        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except JWTError:
            session.clear()
            flash("Сессия истекла, войдите снова", "warning")
            return redirect(url_for("auth.login"))

        # Make payload available as g.user throughout the request
        g.user = payload
        g.permissions = set(payload.get("permissions", []))


def require_permission(code: str):
    """Decorator: abort 403 if the current user lacks the given permission."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if code not in getattr(g, "permissions", set()):
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def has_permission(code: str) -> bool:
    """Template helper: check permission without raising."""
    return code in getattr(g, "permissions", set())
