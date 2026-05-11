"""
Фича: жизненный цикл заказа.

CREATED -> IN_PROGRESS -> READY -> CLOSED
                       \\-> CANCELLED (из любого нетерминального состояния)
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest


def make_order_payload(mock_dish_id: str, table: int = 1, qty: int = 2) -> dict:
    return {
        "table_number": table,
        "customer_name": "Test Customer",
        "items": [{"dish_id": mock_dish_id, "quantity": qty}],
    }


class TestFeatureCreateOrder:
    def test_create_order_returns_201(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        payload = make_order_payload(dish["id"])
        resp = client.post("/api/v1/orders/", json=payload)
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "CREATED"
        assert body["table_number"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["dish_name"] == dish["name"]

    def test_create_order_calculates_total(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        resp = client.post(
            "/api/v1/orders/",
            json=make_order_payload(dish["id"], qty=2),
        )
        body = resp.get_json()
        # 150.00 × 2 = 300.00
        assert float(body["total_amount"]) == 300.0

    def test_create_order_empty_items_returns_422(self, client) -> None:
        resp = client.post("/api/v1/orders/", json={"table_number": 1, "items": []})
        assert resp.status_code == 422

    def test_create_order_without_items_returns_422(self, client) -> None:
        resp = client.post("/api/v1/orders/", json={"table_number": 2})
        assert resp.status_code == 422

    def test_order_snapshots_dish_price(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        item = resp.get_json()["items"][0]
        assert item["price_at_order"] == dish["price"]


class TestFeatureOrderRead:
    def test_get_order_by_id(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        create_resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        order_id = create_resp.get_json()["id"]
        resp = client.get(f"/api/v1/orders/{order_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == order_id

    def test_get_nonexistent_order_returns_404(self, client) -> None:
        resp = client.get(f"/api/v1/orders/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_list_orders(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        resp = client.get("/api/v1/orders/")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_filter_orders_by_status(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        resp = client.get("/api/v1/orders/?status=CREATED")
        orders = resp.get_json()
        assert all(o["status"] == "CREATED" for o in orders)


class TestFeatureOrderStatusLifecycle:
    """Полный жизненный цикл: CREATED -> IN_PROGRESS -> READY -> CLOSED."""

    def _create(self, client, mock_menu_service) -> str:
        _, dish = mock_menu_service
        resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        return resp.get_json()["id"]

    def test_take_order_transitions_to_in_progress(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        resp = client.post(f"/api/v1/orders/{order_id}/take")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "IN_PROGRESS"
        assert resp.get_json()["taken_at"] is not None

    def test_mark_order_ready(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        client.post(f"/api/v1/orders/{order_id}/take")
        resp = client.post(f"/api/v1/orders/{order_id}/ready")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "READY"

    def test_close_order(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        client.post(f"/api/v1/orders/{order_id}/take")
        client.post(f"/api/v1/orders/{order_id}/ready")
        resp = client.post(f"/api/v1/orders/{order_id}/close")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "CLOSED"
        assert body["closed_at"] is not None

    def test_cancel_created_order(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        resp = client.post(f"/api/v1/orders/{order_id}/cancel")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "CANCELLED"

    def test_cancel_in_progress_order(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        client.post(f"/api/v1/orders/{order_id}/take")
        resp = client.post(f"/api/v1/orders/{order_id}/cancel")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "CANCELLED"

    def test_invalid_transition_returns_422(self, client, mock_menu_service) -> None:
        # нельзя перейти напрямую из CREATED в CLOSED
        order_id = self._create(client, mock_menu_service)
        resp = client.patch(
            f"/api/v1/orders/{order_id}/status", json={"status": "CLOSED"}
        )
        assert resp.status_code == 422

    def test_closed_order_cannot_be_cancelled(self, client, mock_menu_service) -> None:
        order_id = self._create(client, mock_menu_service)
        client.post(f"/api/v1/orders/{order_id}/take")
        client.post(f"/api/v1/orders/{order_id}/ready")
        client.post(f"/api/v1/orders/{order_id}/close")
        resp = client.post(f"/api/v1/orders/{order_id}/cancel")
        assert resp.status_code == 422


class TestFeatureOrderDelete:
    def test_delete_order_returns_204(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        create_resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        order_id = create_resp.get_json()["id"]
        resp = client.delete(f"/api/v1/orders/{order_id}")
        assert resp.status_code == 204

    def test_delete_removes_order(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        create_resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        order_id = create_resp.get_json()["id"]
        client.delete(f"/api/v1/orders/{order_id}")
        assert client.get(f"/api/v1/orders/{order_id}").status_code == 404


# ── Фикстуры: интеграция со складом ──────────────────────────────────────────

_PRODUCT_ID = str(uuid.uuid4())
_DISH_WITH_INGREDIENTS_ID = str(uuid.uuid4())

_DISH_WITH_INGREDIENTS = {
    "id": _DISH_WITH_INGREDIENTS_ID,
    "name": "Chicken Curry",
    "price": "250.00",
    "is_available": True,
}
_INGREDIENTS = [
    {
        "product_id": _PRODUCT_ID,
        "product_name": "Chicken",
        "quantity": "0.300",
        "unit": "kg",
    }
]


def _make_stock_side_effect(stock: str):
    def _side_effect(url: str, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.status_code = 200
        if "/ingredients" in url:
            resp.json.return_value = _INGREDIENTS
        elif "/products/" in url:
            resp.json.return_value = {"id": _PRODUCT_ID, "current_stock": stock}
        else:
            resp.json.return_value = _DISH_WITH_INGREDIENTS
        return resp
    return _side_effect


@pytest.fixture()
def mock_sufficient_stock():
    with patch("httpx.get", side_effect=_make_stock_side_effect("10.000")):
        with patch("httpx.post", return_value=MagicMock(status_code=200)):
            yield _DISH_WITH_INGREDIENTS_ID


@pytest.fixture()
def mock_insufficient_stock():
    with patch("httpx.get", side_effect=_make_stock_side_effect("0.100")):
        with patch("httpx.post", return_value=MagicMock(status_code=200)):
            yield _DISH_WITH_INGREDIENTS_ID


# ── Проверка наличия остатков ─────────────────────────────────────────────────

class TestFeatureStockFeasibility:
    """Нельзя создать заказ, если ингредиентов не хватает."""

    def test_order_with_sufficient_stock_succeeds(self, client, mock_sufficient_stock) -> None:
        resp = client.post("/api/v1/orders/", json=make_order_payload(mock_sufficient_stock))
        assert resp.status_code == 201

    def test_order_with_insufficient_stock_returns_422(self, client, mock_insufficient_stock) -> None:
        # 100 порций × 0.3 кг = 30 кг нужно, на складе только 0.1 кг
        payload = make_order_payload(mock_insufficient_stock, qty=100)
        resp = client.post("/api/v1/orders/", json=payload)
        assert resp.status_code == 422
        assert "Недостаточно продуктов на складе" in resp.get_json()["detail"]

    def test_insufficient_stock_error_names_the_product(self, client, mock_insufficient_stock) -> None:
        payload = make_order_payload(mock_insufficient_stock, qty=100)
        resp = client.post("/api/v1/orders/", json=payload)
        assert "Chicken" in resp.get_json()["detail"]

    def test_order_without_ingredients_always_succeeds(self, client, mock_menu_service) -> None:
        _, dish = mock_menu_service
        resp = client.post("/api/v1/orders/", json=make_order_payload(dish["id"]))
        assert resp.status_code == 201


class TestFeatureIngredientSnapshot:
    """Ингредиенты снимаются со склада при переходе в READY."""

    def test_ready_transition_calls_warehouse_deduction(self, client, mock_sufficient_stock) -> None:
        dish_id = mock_sufficient_stock
        create_resp = client.post("/api/v1/orders/", json=make_order_payload(dish_id))
        assert create_resp.status_code == 201
        order_id = create_resp.get_json()["id"]
        client.post(f"/api/v1/orders/{order_id}/take")

        with patch("httpx.post") as deduct_mock:
            deduct_mock.return_value = MagicMock(status_code=200)
            resp = client.post(f"/api/v1/orders/{order_id}/ready")

        assert resp.status_code == 200
        assert resp.get_json()["status"] == "READY"
        deduct_mock.assert_called_once()
        call_json = deduct_mock.call_args.kwargs["json"]
        assert call_json["movement_type"] == "OUTGOING"

    def test_close_does_not_call_warehouse_again(self, client, mock_sufficient_stock) -> None:
        dish_id = mock_sufficient_stock
        create_resp = client.post("/api/v1/orders/", json=make_order_payload(dish_id))
        order_id = create_resp.get_json()["id"]
        client.post(f"/api/v1/orders/{order_id}/take")
        client.post(f"/api/v1/orders/{order_id}/ready")

        with patch("httpx.post") as close_mock:
            close_mock.return_value = MagicMock(status_code=200)
            resp = client.post(f"/api/v1/orders/{order_id}/close")

        assert resp.status_code == 200
        close_mock.assert_not_called()
