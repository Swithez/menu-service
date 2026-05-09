"""
Pydantic schemas for order-service.
Used for request validation (type-driven) and response serialisation.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import ClassVar

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

    ALLOWED_TRANSITIONS: ClassVar[dict[OrderStatus, set[OrderStatus]]] = {
        OrderStatus.CREATED: {OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED},
        OrderStatus.IN_PROGRESS: {OrderStatus.READY, OrderStatus.CANCELLED},
        OrderStatus.READY: {OrderStatus.CLOSED},
        OrderStatus.CLOSED: set(),
        OrderStatus.CANCELLED: set(),
    }

    _STATUS_RU: ClassVar[dict[str, str]] = {
        "CREATED": "Создан",
        "IN_PROGRESS": "В работе",
        "READY": "Готово к выдаче",
        "CLOSED": "Закрыт",
        "CANCELLED": "Отменён",
    }

    @classmethod
    def validate_transition(cls, current: OrderStatus, next_status: OrderStatus) -> None:
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        if next_status not in allowed:
            cur_ru = cls._STATUS_RU.get(current.value, current.value)
            nxt_ru = cls._STATUS_RU.get(next_status.value, next_status.value)
            if allowed:
                allowed_ru = ", ".join(
                    cls._STATUS_RU.get(s.value, s.value) for s in allowed
                )
                raise ValueError(
                    f"Нельзя перевести заказ из «{cur_ru}» в «{nxt_ru}». "
                    f"Доступные переходы: {allowed_ru}"
                )
            else:
                raise ValueError(
                    f"Заказ в статусе «{cur_ru}» — финальное состояние, изменение невозможно"
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
