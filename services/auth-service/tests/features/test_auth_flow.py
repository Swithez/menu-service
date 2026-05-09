"""
Фича: аутентификация через JWT.
"""
import pytest


class TestFeatureLogin:
    """Вход по email и паролю."""

    async def test_login_valid_credentials_returns_200(self, client) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "testpass123"},
        )
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
        """Токен должен быть трёхсегментным JWT."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "testpass123"},
        )
        token = resp.json()["access_token"]
        assert token.count(".") == 2, "ожидается три сегмента (header.payload.sig)"


class TestFeatureMe:
    """GET /me — данные текущего пользователя."""

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
        """Токен admin должен содержать непустой список прав."""
        # логинимся заново, чтобы проверить payload
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
    """Проверка работоспособности сервиса."""

    async def test_health_returns_ok(self, client) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
