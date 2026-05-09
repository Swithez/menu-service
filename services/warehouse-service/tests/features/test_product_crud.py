"""
Фича: управление продуктами на складе.
"""
import pytest


class TestFeatureProductCreate:
    async def test_create_product_returns_201(self, client) -> None:
        payload = {"name": "Beef", "unit": "kg", "cost_price": "450.00", "min_stock_level": "5.000"}
        resp = await client.post("/api/v1/products/", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Beef"
        assert body["unit"] == "kg"
        assert float(body["current_stock"]) == 0.0

    async def test_create_product_with_initial_stock(self, client) -> None:
        payload = {"name": "Chicken", "unit": "kg", "initial_stock": "20.000"}
        resp = await client.post("/api/v1/products/", json=payload)
        assert resp.status_code == 201
        assert float(resp.json()["current_stock"]) == 20.0

    async def test_create_duplicate_product_returns_409(self, client) -> None:
        payload = {"name": "Pork", "unit": "kg"}
        await client.post("/api/v1/products/", json=payload)
        resp = await client.post("/api/v1/products/", json=payload)
        assert resp.status_code == 409

    async def test_create_invalid_unit_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/products/", json={"name": "X", "unit": "barrels"})
        assert resp.status_code == 422


class TestFeatureStockManagement:
    """Корректировка остатков с историей движений."""

    async def test_incoming_stock_increases_level(self, client) -> None:
        # продукт с нулевым остатком
        create_resp = await client.post("/api/v1/products/", json={"name": "Tomato", "unit": "kg"})
        pid = create_resp.json()["id"]
        # приёмка
        resp = await client.post(
            f"/api/v1/products/{pid}/stock",
            json={"quantity": "15.500", "movement_type": "INCOMING"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["current_stock"]) == 15.5

    async def test_outgoing_stock_decreases_level(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/products/", json={"name": "Onion", "unit": "kg", "initial_stock": "10.000"}
        )
        pid = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/products/{pid}/stock",
            json={"quantity": "3.000", "movement_type": "OUTGOING", "reason": "Kitchen use"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["current_stock"]) == 7.0

    async def test_insufficient_stock_returns_422(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/products/", json={"name": "Pepper", "unit": "g", "initial_stock": "100.000"}
        )
        pid = create_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/products/{pid}/stock",
            json={"quantity": "500.000", "movement_type": "OUTGOING", "reason": "Overdraft test"},
        )
        assert resp.status_code == 422

    async def test_stock_movements_are_recorded(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/products/", json={"name": "Carrot", "unit": "kg", "initial_stock": "5.000"}
        )
        pid = create_resp.json()["id"]
        await client.post(
            f"/api/v1/products/{pid}/stock",
            json={"quantity": "10.000", "movement_type": "INCOMING"},
        )
        movements_resp = await client.get(f"/api/v1/products/{pid}/movements")
        assert movements_resp.status_code == 200
        # начальный остаток + вторая приёмка
        assert len(movements_resp.json()) >= 2

    async def test_low_stock_filter(self, client) -> None:
        # 0 остатка при минимуме 5 — должен попасть в фильтр
        await client.post(
            "/api/v1/products/",
            json={"name": "RareSauce", "unit": "ml", "min_stock_level": "5.000"},
        )
        resp = await client.get("/api/v1/products/?low_stock_only=true")
        names = [p["name"] for p in resp.json()]
        assert "RareSauce" in names


class TestFeatureProductRead:
    async def test_list_products(self, client) -> None:
        resp = await client.get("/api/v1/products/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_product_by_id(self, client) -> None:
        create_resp = await client.post("/api/v1/products/", json={"name": "Garlic", "unit": "g"})
        pid = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/products/{pid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    async def test_get_nonexistent_product_returns_404(self, client) -> None:
        resp = await client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestFeatureProductDelete:
    async def test_delete_product(self, client) -> None:
        create_resp = await client.post("/api/v1/products/", json={"name": "Temp", "unit": "pcs"})
        pid = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/products/{pid}")
        assert resp.status_code == 204
        # проверяем, что удалился
        assert (await client.get(f"/api/v1/products/{pid}")).status_code == 404
