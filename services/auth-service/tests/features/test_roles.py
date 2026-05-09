"""
Фича: управление ролями.
"""
import pytest


FAKE_ID = "00000000-0000-0000-0000-000000000000"


class TestFeatureRoleList:
    """Список ролей."""

    async def test_list_roles_returns_200(self, admin_client) -> None:
        resp = await admin_client.get("/api/v1/roles")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_roles_contains_admin(self, admin_client) -> None:
        resp = await admin_client.get("/api/v1/roles")
        names = [r["name"] for r in resp.json()]
        assert "admin" in names

    async def test_list_roles_unauthenticated_returns_401(self, client) -> None:
        resp = await client.get("/api/v1/roles")
        assert resp.status_code in (401, 403)


class TestFeatureRoleCreate:
    """Создание роли."""

    async def test_create_role_returns_201(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/roles",
            json={"name": "waiter", "description": "Waiter role"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "waiter"
        assert body["is_system"] is False
        assert isinstance(body["permissions"], list)

    async def test_create_role_with_permissions(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/roles",
            json={
                "name": "menu-reader",
                "permission_codes": ["menu:dishes:read", "menu:categories:read"],
            },
        )
        assert resp.status_code == 201
        codes = [p["code"] for p in resp.json()["permissions"]]
        assert "menu:dishes:read" in codes
        assert "menu:categories:read" in codes

    async def test_create_duplicate_role_returns_409(self, admin_client) -> None:
        await admin_client.post("/api/v1/roles", json={"name": "duplicate-role"})
        resp = await admin_client.post("/api/v1/roles", json={"name": "duplicate-role"})
        assert resp.status_code == 409

    async def test_create_role_blank_name_returns_422(self, admin_client) -> None:
        resp = await admin_client.post("/api/v1/roles", json={"name": "   "})
        assert resp.status_code == 422

    async def test_create_role_unknown_permission_returns_409(self, admin_client) -> None:
        resp = await admin_client.post(
            "/api/v1/roles",
            json={"name": "bad-perms-role", "permission_codes": ["fake:permission:code"]},
        )
        assert resp.status_code == 409


class TestFeatureRoleRead:
    """Чтение роли."""

    async def test_get_role_returns_detail(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "chef"})
        role_id = create_resp.json()["id"]
        resp = await admin_client.get(f"/api/v1/roles/{role_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "chef"
        assert "permissions" in resp.json()

    async def test_get_nonexistent_role_returns_404(self, admin_client) -> None:
        resp = await admin_client.get(f"/api/v1/roles/{FAKE_ID}")
        assert resp.status_code == 404

    async def test_get_admin_role_is_system(self, admin_client) -> None:
        roles = await admin_client.get("/api/v1/roles")
        admin = next(r for r in roles.json() if r["name"] == "admin")
        detail = await admin_client.get(f"/api/v1/roles/{admin['id']}")
        assert detail.json()["is_system"] is True


class TestFeatureRoleUpdate:
    """Обновление роли."""

    async def test_update_role_name(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "old-name"})
        role_id = create_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/roles/{role_id}", json={"name": "new-name"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "new-name"

    async def test_update_role_description(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "desc-role"})
        role_id = create_resp.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/roles/{role_id}", json={"description": "Updated description"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    async def test_update_nonexistent_role_returns_404(self, admin_client) -> None:
        resp = await admin_client.patch(
            f"/api/v1/roles/{FAKE_ID}", json={"name": "x"}
        )
        assert resp.status_code == 404

    async def test_update_to_duplicate_name_returns_409(self, admin_client) -> None:
        await admin_client.post("/api/v1/roles", json={"name": "role-alpha"})
        r2 = await admin_client.post("/api/v1/roles", json={"name": "role-beta"})
        role_id = r2.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/roles/{role_id}", json={"name": "role-alpha"}
        )
        assert resp.status_code == 409


class TestFeatureRolePermissions:
    """Назначение прав роли."""

    async def test_set_permissions_replaces_all(self, admin_client) -> None:
        # роль с одним правом
        create_resp = await admin_client.post(
            "/api/v1/roles",
            json={"name": "perm-test-role", "permission_codes": ["menu:dishes:read"]},
        )
        role_id = create_resp.json()["id"]
        # заменяем на другой набор
        resp = await admin_client.put(
            f"/api/v1/roles/{role_id}/permissions",
            json=["menu:categories:read", "orders:create"],
        )
        assert resp.status_code == 200
        codes = {p["code"] for p in resp.json()["permissions"]}
        assert codes == {"menu:categories:read", "orders:create"}
        assert "menu:dishes:read" not in codes

    async def test_set_empty_permissions_clears_all(self, admin_client) -> None:
        create_resp = await admin_client.post(
            "/api/v1/roles",
            json={"name": "clear-perm-role", "permission_codes": ["orders:create"]},
        )
        role_id = create_resp.json()["id"]
        resp = await admin_client.put(f"/api/v1/roles/{role_id}/permissions", json=[])
        assert resp.status_code == 200
        assert resp.json()["permissions"] == []

    async def test_set_invalid_permission_code_returns_422(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "bad-code-role"})
        role_id = create_resp.json()["id"]
        resp = await admin_client.put(
            f"/api/v1/roles/{role_id}/permissions", json=["totally:fake:code"]
        )
        assert resp.status_code == 422


class TestFeatureRoleDelete:
    """Удаление роли."""

    async def test_delete_non_system_role_returns_204(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "deletable-role"})
        role_id = create_resp.json()["id"]
        resp = await admin_client.delete(f"/api/v1/roles/{role_id}")
        assert resp.status_code == 204

    async def test_deleted_role_returns_404(self, admin_client) -> None:
        create_resp = await admin_client.post("/api/v1/roles", json={"name": "gone-role"})
        role_id = create_resp.json()["id"]
        await admin_client.delete(f"/api/v1/roles/{role_id}")
        resp = await admin_client.get(f"/api/v1/roles/{role_id}")
        assert resp.status_code == 404

    async def test_delete_system_role_returns_409(self, admin_client) -> None:
        roles = await admin_client.get("/api/v1/roles")
        admin_role = next(r for r in roles.json() if r["name"] == "admin")
        resp = await admin_client.delete(f"/api/v1/roles/{admin_role['id']}")
        assert resp.status_code == 409

    async def test_delete_nonexistent_role_returns_404(self, admin_client) -> None:
        resp = await admin_client.delete(f"/api/v1/roles/{FAKE_ID}")
        assert resp.status_code == 404
