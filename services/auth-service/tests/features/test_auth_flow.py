"""
Feature: Authentication flow
  As a system user
  I want to obtain a JWT token by logging in
  So that I can make authenticated API calls
"""
import pytest


class TestFeatureLogin:
    """Feature: Login with email + password."""

    async def test_login_valid_credentials_returns_200(self, client) -> None:
        # Given: valid admin credentials
        # When: POST /api/v1/auth/login
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "testpass123"},
        )
        # Then: 200 + token payload
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert isinstance(body["expires_in"], int)
        assert body["expires_in"] > 0

    async def test_login_wrong_password_returns_401(self, client) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_email_returns_401(self, client) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@nowhere.com", "password": "anything"},
        )
        assert resp.status_code == 401

    async def test_login_invalid_email_format_returns_422(self, client) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "pass"},
        )
        assert resp.status_code == 422

    async def test_login_missing_password_returns_422(self, client) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com"},
        )
        assert resp.status_code == 422

    async def test_login_returns_bearer_token(self, client) -> None:
        """Token must be a non-trivial string (three JWT segments)."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "testpass123"},
        )
        token = resp.json()["access_token"]
        assert token.count(".") == 2, "JWT must have three segments"


class TestFeatureMe:
    """Feature: GET /me — current user info from token."""

    async def test_me_with_valid_token_returns_200(self, admin_client) -> None:
        resp = await admin_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "admin@example.com"
        assert body["is_active"] is True
        assert body["role_name"] == "admin"

    async def test_me_without_token_returns_403_or_401(self, client) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    async def test_me_with_invalid_token_returns_401(self, client) -> None:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert resp.status_code == 401

    async def test_me_contains_permissions(self, admin_client) -> None:
        """Admin token must carry a non-empty permissions list."""
        # Login fresh to inspect token payload
        login_resp = await admin_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "testpass123"},
        )
        from jose import jwt
        from app.config import settings
        payload = jwt.decode(
            login_resp.json()["access_token"],
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        assert len(payload["permissions"]) > 0
        assert "users:roles:manage" in payload["permissions"]


class TestFeatureHealth:
    """Feature: Health check endpoint."""

    async def test_health_returns_ok(self, client) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
