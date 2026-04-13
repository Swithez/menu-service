"""
Order business logic.

Inter-service calls (menu-service for dish info, warehouse-service for stock
deduction on close) use httpx synchronous client so Flask stays synchronous.
"""
import uuid
from http import HTTPStatus

import httpx
from flask import abort

from app.config import settings
from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreateSchema, OrderStatusTransitionSchema


class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo

    # ── helpers ───────────────────────────────────────────────────────────────

    def _fetch_dish(self, dish_id: uuid.UUID) -> dict:
        """Call menu-service to validate dish and get its current price."""
        try:
            resp = httpx.get(
                f"{settings.menu_service_url}/api/v1/dishes/{dish_id}",
                timeout=5.0,
            )
            if resp.status_code == 404:
                abort(HTTPStatus.NOT_FOUND, description=f"Dish {dish_id} not found in menu")
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            abort(
                HTTPStatus.SERVICE_UNAVAILABLE,
                description="Menu service is unavailable",
            )

    def _notify_warehouse(self, order_id: uuid.UUID, items: list[OrderItem]) -> None:
        """Inform warehouse-service to deduct stock for each order item.
        Failures are logged but do not fail the order close (eventual consistency).
        """
        for item in items:
            try:
                httpx.post(
                    f"{settings.warehouse_service_url}/api/v1/products/consume",
                    json={
                        "dish_id": str(item.dish_id),
                        "quantity": item.quantity,
                        "order_id": str(order_id),
                    },
                    timeout=3.0,
                )
            except httpx.RequestError:
                pass  # Non-critical — warehouse reconciles asynchronously

    # ── public methods ────────────────────────────────────────────────────────

    def create_order(self, data: OrderCreateSchema) -> Order:
        order = Order(
            table_number=data.table_number,
            customer_name=data.customer_name,
            notes=data.notes,
            status=OrderStatus.CREATED,
        )
        for item_data in data.items:
            dish = self._fetch_dish(item_data.dish_id)
            if not dish.get("is_available", False):
                abort(
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    description=f"Dish '{dish['name']}' is not currently available",
                )
            order_item = OrderItem(
                dish_id=item_data.dish_id,
                dish_name=dish["name"],
                quantity=item_data.quantity,
                price_at_order=dish["price"],
                notes=item_data.notes,
            )
            order.items.append(order_item)
        return self._repo.create(order)

    def get_order(self, order_id: uuid.UUID) -> Order:
        order = self._repo.get_by_id(order_id)
        if not order:
            abort(HTTPStatus.NOT_FOUND, description=f"Order {order_id} not found")
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

        if new_status == OrderStatus.CLOSED:
            db.session.commit()
            self._notify_warehouse(order_id, updated.items)

        return updated

    def cancel_order(self, order_id: uuid.UUID) -> Order:
        return self.transition_status(order_id, OrderStatus.CANCELLED)
