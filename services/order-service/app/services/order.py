"""
Order business logic.

Inter-service calls:
  - menu-service: validate dish + fetch ingredients
  - warehouse-service: check stock feasibility + deduct on READY
"""
import uuid
from decimal import Decimal
from http import HTTPStatus

import httpx
from flask import abort


def _fmt_qty(qty: Decimal) -> str:
    """Format quantity without scientific notation and trailing zeros."""
    f = float(qty)
    if f == int(f):
        return str(int(f))
    return f"{f:.3f}".rstrip("0").rstrip(".")

from app.config import settings
from app.extensions import db
from app.models.order import Order, OrderIngredient, OrderItem, OrderStatus
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreateSchema, OrderStatusTransitionSchema


class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    # ── inter-service helpers ──────────────────────────────────────────────���──

    def _fetch_dish(self, dish_id: uuid.UUID) -> dict:
        """Validate dish and get its current price from menu-service."""
        try:
            resp = httpx.get(
                f"{settings.menu_service_url}/api/v1/dishes/{dish_id}",
                timeout=5.0,
            )
            if resp.status_code == 404:
                abort(HTTPStatus.NOT_FOUND, description=f"Блюдо {dish_id} не найдено в меню")
            resp.raise_for_status()
            return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            abort(HTTPStatus.SERVICE_UNAVAILABLE, description="Сервис меню недоступен")

    def _fetch_dish_ingredients(self, dish_id: uuid.UUID) -> list[dict]:
        """Fetch ingredient list for a dish from menu-service. Returns [] on any error."""
        try:
            resp = httpx.get(
                f"{settings.menu_service_url}/api/v1/dishes/{dish_id}/ingredients",
                timeout=5.0,
            )
            if resp.status_code != 200:
                return []
            return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            return []

    def _fetch_product_stock(self, product_id: str) -> Decimal | None:
        """Get current stock for a product from warehouse-service. Returns None on error."""
        try:
            resp = httpx.get(
                f"{settings.warehouse_service_url}/api/v1/products/{product_id}",
                timeout=5.0,
            )
            if resp.status_code != 200:
                return None
            return Decimal(str(resp.json()["current_stock"]))
        except (httpx.RequestError, httpx.HTTPStatusError):
            return None

    def _deduct_stock(self, order: Order) -> None:
        """Deduct ingredients from warehouse when order moves to READY. Non-blocking."""
        for oi in order.ingredients:
            try:
                httpx.post(
                    f"{settings.warehouse_service_url}/api/v1/products/{oi.product_id}/stock",
                    json={
                        "quantity": float(oi.quantity),
                        "movement_type": "OUTGOING",
                        "reason": f"Заказ #{str(order.id)[:8]}",
                        "order_id": str(order.id),
                    },
                    timeout=5.0,
                )
            except httpx.RequestError:
                pass  # non-blocking — warehouse reconciles independently

    # ── stock feasibility check ───────────────────────────────────────────────

    def _aggregate_ingredients(self, items: list[OrderItem]) -> dict[str, dict]:
        """
        Fetch and aggregate all ingredients required for the given items.
        Returns: {product_id_str: {qty, name, unit}}
        """
        required: dict[str, dict] = {}
        for item in items:
            for ing in self._fetch_dish_ingredients(item.dish_id):
                pid = str(ing["product_id"])
                qty_per = Decimal(str(ing["quantity"])) * item.quantity
                if pid not in required:
                    required[pid] = {
                        "qty": Decimal("0"),
                        "name": ing["product_name"],
                        "unit": ing["unit"],
                    }
                required[pid]["qty"] += qty_per
        return required

    def _reserved_by_active_orders(self) -> dict[str, Decimal]:
        """Sum ingredient quantities already reserved by CREATED/IN_PROGRESS orders."""
        rows = (
            db.session.query(
                OrderIngredient.product_id,
                db.func.sum(OrderIngredient.quantity).label("total"),
            )
            .join(Order, OrderIngredient.order_id == Order.id)
            .filter(Order.status.in_([OrderStatus.CREATED, OrderStatus.IN_PROGRESS]))
            .group_by(OrderIngredient.product_id)
            .all()
        )
        return {str(row.product_id): Decimal(str(row.total)) for row in rows}

    def _check_stock_feasibility(self, required: dict[str, dict]) -> None:
        """Raise 422 if current stock minus active-order reservations is insufficient."""
        if not required:
            return

        reserved = self._reserved_by_active_orders()
        shortages = []

        for pid, info in required.items():
            current = self._fetch_product_stock(pid)
            if current is None:
                continue  # warehouse unavailable for this product — skip
            available = current - reserved.get(pid, Decimal("0"))
            if available < info["qty"]:
                shortages.append(
                    f"{info['name']}: нужно {_fmt_qty(info['qty'])} {info['unit']}, "
                    f"доступно {_fmt_qty(max(Decimal('0'), available))} {info['unit']}"
                )

        if shortages:
            abort(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                description="Недостаточно продуктов на складе: " + "; ".join(shortages),
            )

    # ── public methods ────────────────────────────────────────────────────────

    def create_order(self, data: OrderCreateSchema) -> Order:
        order = Order(
            table_number=data.table_number,
            customer_name=data.customer_name,
            notes=data.notes,
            status=OrderStatus.CREATED,
        )

        # Build items and validate each dish
        for item_data in data.items:
            dish = self._fetch_dish(item_data.dish_id)
            if not dish.get("is_available", False):
                abort(
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    description=f"Блюдо «{dish['name']}» недоступно для заказа",
                )
            order.items.append(OrderItem(
                dish_id=item_data.dish_id,
                dish_name=dish["name"],
                quantity=item_data.quantity,
                price_at_order=Decimal(str(dish["price"])),
                notes=item_data.notes,
            ))

        # Aggregate ingredients and check stock feasibility
        required = self._aggregate_ingredients(order.items)
        self._check_stock_feasibility(required)

        # Persist order
        self._repo.create(order)

        # Snapshot ingredient requirements for future reservation tracking and deduction
        for pid, info in required.items():
            db.session.add(OrderIngredient(
                order_id=order.id,
                product_id=uuid.UUID(pid),
                product_name=info["name"],
                unit=info["unit"],
                quantity=info["qty"],
            ))
        db.session.flush()

        return order

    def get_order(self, order_id: uuid.UUID) -> Order:
        order = self._repo.get_by_id(order_id)
        if not order:
            abort(HTTPStatus.NOT_FOUND, description=f"Заказ {order_id} не найден")
        return order  # type: ignore[return-value]

    def list_orders(
        self,
        *,
        status: OrderStatus | None = None,
        table_number: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        return self._repo.list_all(
            status=status, table_number=table_number, limit=limit, offset=offset
        )

    def transition_status(self, order_id: uuid.UUID, new_status: OrderStatus) -> Order:
        order = self.get_order(order_id)
        try:
            updated = self._repo.transition_status(order, new_status)
        except ValueError as exc:
            abort(HTTPStatus.UNPROCESSABLE_ENTITY, description=str(exc))
            raise  # unreachable — satisfies mypy

        if new_status == OrderStatus.READY:
            # Deduct ingredients from warehouse stock
            db.session.commit()
            self._deduct_stock(updated)

        return updated

    def cancel_order(self, order_id: uuid.UUID) -> Order:
        return self.transition_status(order_id, OrderStatus.CANCELLED)
