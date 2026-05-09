import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db


class OrderIngredient(db.Model):  # type: ignore[name-defined]
    __tablename__ = "order_ingredients"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(UUID(as_uuid=True), nullable=False)
    product_name = db.Column(String(255), nullable=False)
    unit = db.Column(String(50), nullable=False)
    quantity = db.Column(Numeric(10, 3), nullable=False)

    order = relationship("Order", back_populates="ingredients")

    def __repr__(self) -> str:
        return f"<OrderIngredient order_id={self.order_id} product={self.product_name!r} qty={self.quantity}>"


class OrderStatus(str, Enum):
    CREATED = "CREATED"          # Order placed, awaiting kitchen
    IN_PROGRESS = "IN_PROGRESS"  # Kitchen took the order
    READY = "READY"              # Dish is ready, awaiting serving
    CLOSED = "CLOSED"            # Delivered and paid
    CANCELLED = "CANCELLED"      # Order cancelled


class Order(db.Model):  # type: ignore[name-defined]
    __tablename__ = "orders"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_number = db.Column(Integer, nullable=True)
    customer_name = db.Column(String(255), nullable=True)
    status = db.Column(
        SAEnum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.CREATED,
    )
    notes = db.Column(Text, nullable=True)
    total_amount = db.Column(Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    taken_at = db.Column(DateTime(timezone=True), nullable=True)
    closed_at = db.Column(DateTime(timezone=True), nullable=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    ingredients = relationship("OrderIngredient", back_populates="order", cascade="all, delete-orphan")

    def recalculate_total(self) -> None:
        self.total_amount = sum(
            (item.price_at_order * item.quantity) for item in self.items
        )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status} total={self.total_amount}>"


class OrderItem(db.Model):  # type: ignore[name-defined]
    __tablename__ = "order_items"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    dish_id = db.Column(UUID(as_uuid=True), nullable=False)
    dish_name = db.Column(String(255), nullable=False)       # snapshot at order time
    quantity = db.Column(Integer, nullable=False, default=1)
    price_at_order = db.Column(Numeric(10, 2), nullable=False)  # snapshot at order time
    notes = db.Column(Text, nullable=True)

    order = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem dish={self.dish_name!r} qty={self.quantity}>"
