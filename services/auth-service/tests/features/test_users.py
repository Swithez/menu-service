"""
Feature: User management
  As an administrator
  I want to create and manage user accounts
  So that staff can access the system with appropriate roles
"""
import pytest


FAKE_ID = "00000000-0000-0000-0000-000000000099"


class TestFeatureUserList:
    """Feature: List users."""

    async def test_list_users_returns_200(self, admin_client) -> None:
        resp = await admin_client.get("/api/v1/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_contains_seeded_admin(self, admin_client) -> None:
        resp = await admin_client.get("/api/v1/users")
        emails = [u["email"] for u in resp.json()]
        assert "admin@example.com" in emails

    async def test_list_users_unauthenticated_returns_401(self, client) -> None:
        resp = await client.get("/api/v1/users")
        assert resp.status_code in (401, 403)


class TestFeatureUserCreate:
    """Feature: Create a new user."""

    async def test_create_user_minimal_returns_201(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/users",
            json={
                "email": "chef@restaurant.com",
                "full_name": "Head Chef",
                "password": "cookmaster1",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "chef@restaurant.com"
        assert body["full_name"] == "Head Chef"
        assert body["is_active"] is True
        assert body["role_id"] is None
        assert "id" in body

    async def test_create_user_with_role(self, admin_client) -> None:
        # Given: a non-system role exists
        role_resp = await admin_client.post(
            "/api/v1/roles", json={"name": "cashier-role"}
        )
        role_id = role_resp.json()["id"]
        # When: create user with that role
        resp = await admin_client.post(
            "/api/v1/users",
            json={
                "email": "cashier@restaurant.com",
                "full_name": "Cashier One",
                "password": "cashpass1",
                "role_id": role_id,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["role_id"] == role_id

    async def test_create_user_duplicate_email_returns_409(self, admin_client) -> None:
        payload = {
            "email": "unique-once@restaurant.com",
            "full_name": "User",
            "password": "pass1234",
        }
        await admin_client.post("/api/v1/users", json=payload)
        resp = await admin_client.post("/api/v1/users", json=payload)
        assert resp.status_code == 409

    async def test_create_user_short_password_returns_422(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "short@pw.com", "full_name": "X", "password": "12345"},
        )
        assert resp.status_code == 422

    async def test_create_user_invalid_email_returns_422(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "not-an-email", "full_name": "X", "password": "pass123"},
        )
        assert resp.status_code == 422

    async def test_create_inactive_user(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/users",
            json={
                "email": "inactive@restaurant.com",
                "full_name": "Inactive",
                "password": "pass1234",
                "is_active": False,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["is_active"] is False


class TestFeatureUserRead:
    """Feature: Read a single user."""

    async def test_get_user_by_id(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "readable@restaurant.com", "full_name": "R", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id

    async def test_get_nonexistent_user_returns_404(self, admin_client) -> None:
        resp = await admin_client.get(f"/api/v1/users/{FAKE_ID}")
        assert resp.status_code == 404


class TestFeatureUserUpdate:
    """Feature: Update user details."""

    async def test_update_full_name(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "name-change@restaurant.com", "full_name": "Old Name", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/users/{user_id}", json={"full_name": "New Name"}
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "New Name"

    async def test_deactivate_user(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "deactivate@restaurant.com", "full_name": "Active", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/users/{user_id}", json={"is_active": False}
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_update_password(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "pw-change@restaurant.com", "full_name": "User", "password": "oldpass1"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/users/{user_id}", json={"password": "newpass1"}
        )
        assert resp.status_code == 200

    async def test_assign_role_to_user(self, admin_client) -> None:
        role_resp = await admin_client.post("/api/v1/roles", json={"name": "assign-role-test"})
        role_id = role_resp.json()["id"]
        user_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "assign-role@restaurant.com", "full_name": "U", "password": "pass1234"},
        )
        user_id = user_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/users/{user_id}", json={"role_id": role_id}
        )
        assert resp.status_code == 200
        assert resp.json()["role_id"] == role_id

    async def test_update_nonexistent_user_returns_404(self, admin_client) -> None:
        resp = await admin_client.patch(
            f"/api/v1/users/{FAKE_ID}", json={"full_name": "Ghost"}
        )
        assert resp.status_code == 404

    async def test_update_empty_body_returns_422(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "empty-update@restaurant.com", "full_name": "U", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.patch(f"/api/v1/users/{user_id}", json={})
        assert resp.status_code == 422


class TestFeatureUserDelete:
    """Feature: Delete a user."""

    async def test_delete_user_returns_204(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "del-me@restaurant.com", "full_name": "Del", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        resp = await admin_client.delete(f"/api/v1/users/{user_id}")
        assert resp.status_code == 204

    async def test_deleted_user_not_found(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={"email": "gone-user@restaurant.com", "full_name": "Gone", "password": "pass1234"},
        )
        user_id = create_resp.json()["id"]
        await admin_client.delete(f"/api/v1/users/{user_id}")
        resp = await admin_client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 404

    async def test_delete_nonexistent_user_returns_404(self, admin_client) -> None:
        resp = await admin_client.delete(f"/api/v1/users/{FAKE_ID}")
        assert resp.status_code == 404


class TestFeatureInactiveUserLogin:
    """Feature: Inactive users cannot log in."""

    async def test_inactive_user_login_returns_403(self, admin_client, client) -> None:
        # Create then deactivate a user
        create_resp = await admin_client.post(
            "/api/v1/users",
            json={
                "email": "blocked@restaurant.com",
                "full_name": "Blocked",
                "password": "blockpass1",
                "is_active": False,
            },
        )
        # Attempt login
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "blocked@restaurant.com", "password": "blockpass1"},
        )
        assert resp.status_code == 403
