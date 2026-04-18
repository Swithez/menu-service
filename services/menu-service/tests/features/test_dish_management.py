"""
Feature: Dish management with price tracking
  As a restaurant manager
  I want to manage dishes with prices
  So that customers can see accurate menu information
"""


class TestFeatureDishCreate:
    """Feature: Create dishes."""

    async def test_create_dish_minimal(self, client) -> None:
        payload = {"name": "Borscht", "price": "120.00"}
        resp = await client.post("/api/v1/dishes/", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Borscht"
        assert body["price"] == "120.00"
        assert body["is_available"] is True

    async def test_create_dish_with_category(self, client) -> None:
        cat_resp = await client.post("/api/v1/categories/", json={"name": "Fish"})
        cat_id = cat_resp.json()["id"]
        resp = await client.post(
            "/api/v1/dishes/", json={"name": "Trout", "price": "650.00", "category_id": cat_id}
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] == cat_id

    async def test_create_dish_with_invalid_category_returns_404(self, client) -> None:
        fake_cat_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/dishes/",
            json={"name": "Orphan Dish", "price": "100.00", "category_id": fake_cat_id},
        )
        assert resp.status_code == 404

    async def test_create_dish_zero_price_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/dishes/", json={"name": "Free", "price": "0"})
        assert resp.status_code == 422

    async def test_create_dish_negative_price_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/dishes/", json={"name": "X", "price": "-50"})
        assert resp.status_code == 422


class TestFeatureDishRead:
    """Feature: Read and filter dishes."""

    async def test_list_dishes_empty(self, client) -> None:
        resp = await client.get("/api/v1/dishes/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_dish_by_id(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Pelmeni", "price": "300.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == dish_id

    async def test_get_nonexistent_dish_returns_404(self, client) -> None:
        resp = await client.get("/api/v1/dishes/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_filter_by_available_only(self, client) -> None:
        await client.post("/api/v1/dishes/", json={"name": "Available Dish", "price": "100", "is_available": True})
        await client.post("/api/v1/dishes/", json={"name": "Unavailable Dish", "price": "100", "is_available": False})
        resp = await client.get("/api/v1/dishes/?available_only=true")
        names = [d["name"] for d in resp.json()]
        assert "Available Dish" in names
        assert "Unavailable Dish" not in names

    async def test_filter_by_category(self, client) -> None:
        cat_resp = await client.post("/api/v1/categories/", json={"name": "Meat"})
        cat_id = cat_resp.json()["id"]
        await client.post("/api/v1/dishes/", json={"name": "Schnitzel", "price": "700", "category_id": cat_id})
        await client.post("/api/v1/dishes/", json={"name": "Salad", "price": "200"})
        resp = await client.get(f"/api/v1/dishes/?category_id={cat_id}")
        names = [d["name"] for d in resp.json()]
        assert "Schnitzel" in names
        assert "Salad" not in names


class TestFeatureDishUpdate:
    """Feature: Update dish details."""

    async def test_mark_dish_unavailable(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Seasonal Dish", "price": "400.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}", json={"is_available": False})
        assert resp.status_code == 200
        assert resp.json()["is_available"] is False

    async def test_update_dish_name(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Old Name", "price": "200.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"


class TestFeaturePriceManagement:
    """Feature: Manage dish prices with history tracking."""

    async def test_update_price_stores_history(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Coffee", "price": "150.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "200.00"})
        assert resp.status_code == 200
        assert resp.json()["price"] == "200.00"
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert len(history) >= 1
        assert history[0]["old_price"] == "150.00"
        assert history[0]["new_price"] == "200.00"

    async def test_update_price_same_value_no_history(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Tea", "price": "80.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "80.00"})
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        assert len(history_resp.json()) == 0

    async def test_multiple_price_changes_recorded(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Latte", "price": "200.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "220.00"})
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "250.00"})
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        history = history_resp.json()
        assert len(history) == 2
        new_prices = {h["new_price"] for h in history}
        assert new_prices == {"220.00", "250.00"}


class TestFeatureDishDelete:
    """Feature: Delete dishes."""

    async def test_delete_dish_returns_204(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Temporary Dish", "price": "50.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 204

    async def test_delete_dish_removes_it(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Gone Dish", "price": "50.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.delete(f"/api/v1/dishes/{dish_id}")
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 404
