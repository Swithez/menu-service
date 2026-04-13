"""
Feature: Category management
  As a restaurant manager
  I want to create, view, update, and delete menu categories
  So that dishes can be organized by type
"""
import pytest


class TestFeatureCategoryCreate:
    """Feature: Create a new category."""

    async def test_create_category_returns_201(self, client) -> None:
        # Given: valid category data
        payload = {"name": "Hot Dishes", "description": "Warm main courses"}
        # When: POST /api/v1/categories/
        resp = await client.post("/api/v1/categories/", json=payload)
        # Then: 201 Created with the new category
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Hot Dishes"
        assert body["description"] == "Warm main courses"
        assert body["is_active"] is True
        assert "id" in body

    async def test_create_duplicate_category_returns_409(self, client) -> None:
        payload = {"name": "Unique Category"}
        await client.post("/api/v1/categories/", json=payload)
        # When: same name again
        resp = await client.post("/api/v1/categories/", json=payload)
        assert resp.status_code == 409

    async def test_create_category_blank_name_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/categories/", json={"name": "   "})
        assert resp.status_code == 422

    async def test_create_category_empty_name_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/categories/", json={"name": ""})
        assert resp.status_code == 422


class TestFeatureCategoryRead:
    """Feature: Read categories."""

    async def test_list_categories_returns_empty(self, client) -> None:
        resp = await client.get("/api/v1/categories/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_category_by_id(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/categories/", json={"name": "Soups", "is_active": True}
        )
        cat_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/categories/{cat_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == cat_id

    async def test_get_nonexistent_category_returns_404(self, client) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/categories/{fake_id}")
        assert resp.status_code == 404

    async def test_list_active_only_filter(self, client) -> None:
        await client.post("/api/v1/categories/", json={"name": "Active Cat", "is_active": True})
        await client.post("/api/v1/categories/", json={"name": "Inactive Cat", "is_active": False})
        resp = await client.get("/api/v1/categories/?active_only=true")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Active Cat" in names
        assert "Inactive Cat" not in names


class TestFeatureCategoryUpdate:
    """Feature: Update a category."""

    async def test_update_category_name(self, client) -> None:
        create_resp = await client.post("/api/v1/categories/", json={"name": "Old Name"})
        cat_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/categories/{cat_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_deactivate_category(self, client) -> None:
        create_resp = await client.post("/api/v1/categories/", json={"name": "To Deactivate"})
        cat_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/categories/{cat_id}", json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_update_nonexistent_category_returns_404(self, client) -> None:
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.patch(f"/api/v1/categories/{fake_id}", json={"name": "X"})
        assert resp.status_code == 404


class TestFeatureCategoryDelete:
    """Feature: Delete a category."""

    async def test_delete_category_returns_204(self, client) -> None:
        create_resp = await client.post("/api/v1/categories/", json={"name": "Deletable"})
        cat_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/categories/{cat_id}")
        assert resp.status_code == 204

    async def test_delete_removes_from_list(self, client) -> None:
        create_resp = await client.post("/api/v1/categories/", json={"name": "Removable"})
        cat_id = create_resp.json()["id"]
        await client.delete(f"/api/v1/categories/{cat_id}")
        resp = await client.get(f"/api/v1/categories/{cat_id}")
        assert resp.status_code == 404

    async def test_delete_nonexistent_returns_404(self, client) -> None:
        fake_id = "00000000-0000-0000-0000-000000000002"
        resp = await client.delete(f"/api/v1/categories/{fake_id}")
        assert resp.status_code == 404
