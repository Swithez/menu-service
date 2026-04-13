import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderStatusTransitionSchema


class OrderRepository:
    """Data-access layer — all DB interactions go through here."""

    def create(self, order: Order) -> Order:
        db.session.add(order)
        db.session.flush()
        order.recalculate_total()
        db.session.flush()
        return order

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        return db.session.get(Order, order_id)

    def list_all(
        self,
        *,
        status: OrderStatus | None = None,
        table_number: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Order]:
        q = Order.query
        if status is not None:
            q = q.filter(Order.status == status)
        if table_number is not None:
            q = q.filter(Order.table_number == table_number)
        return q.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()

    def transition_status(self, order: Order, new_status: OrderStatus) -> Order:
        OrderStatusTransitionSchema.validate_transition(order.status, new_status)
        order.status = new_status
        now = datetime.now(timezone.utc)
        if new_status == OrderStatus.IN_PROGRESS:
            order.taken_at = now
        elif new_status in (OrderStatus.CLOSED, OrderStatus.CANCELLED):
            order.closed_at = now
        order.updated_at = now
        db.session.flush()
        return order

    def add_item(self, order: Order, item: OrderItem) -> Order:
        order.items.append(item)
        order.recalculate_total()
        order.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return order

    def remove_item(self, order: Order, item_id: uuid.UUID) -> Order:
        item = next((i for i in order.items if i.id == item_id), None)
        if item:
            order.items.remove(item)
            db.session.delete(item)
            order.recalculate_total()
            order.updated_at = datetime.now(timezone.utc)
            db.session.flush()
        return order

    def delete(self, order: Order) -> None:
        db.session.delete(order)
        db.session.flush()
