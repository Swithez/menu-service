"""
Pydantic schemas for order-service.
Used for request validation (type-driven) and response serialisation.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    dish_id: uuid.UUID
    quantity: int = Field(..., ge=1, le=100, description="Number of portions")
    notes: str | None = Field(None, max_length=500)

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        return v


class OrderCreateSchema(BaseModel):
    table_number: int | None = Field(None, ge=1, le=999)
    customer_name: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=1000)
    items: list[OrderItemCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def items_not_empty(self) -> "OrderCreateSchema":
        if not self.items:
            raise ValueError("Order must contain at least one item")
        return self


class OrderStatusTransitionSchema(BaseModel):
    """Explicit status transition — validates allowed transitions."""

    status: OrderStatus

    ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.CREATED: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED},
        OrderStatus.IN_PROGRESS: {OrderStatus.READY, OrderStatus.CANCELLED},
        OrderStatus.READY: {OrderStatus.CLOSED},
        OrderStatus.CLOSED: set(),
        OrderStatus.CANCELLED: set(),
    }

    @classmethod
    def validate_transition(cls, current: OrderStatus, next_status: OrderStatus) -> None:
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        if next_status not in allowed:
            raise ValueError(
                f"Cannot transition from {current} to {next_status}. "
                f"Allowed: {allowed or 'none (terminal state)'}"
            )


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dish_id: uuid.UUID
    dish_name: str
    quantity: int
    price_at_order: Decimal
    notes: str | None


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    table_number: int | None
    customer_name: str | None
    status: OrderStatus
    notes: str | None
    total_amount: Decimal
    items: list[OrderItemSchema]
    created_at: datetime
    updated_at: datetime
    taken_at: datetime | None
    closed_at: datetime | None
