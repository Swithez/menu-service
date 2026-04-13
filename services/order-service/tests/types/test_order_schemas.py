"""
Type-driven tests for order-service schemas.
Validates Pydantic constraints without touching DB or HTTP.
"""
import uuid

import pytest
from pydantic import ValidationError

from app.models.order import OrderStatus
from app.schemas.order import OrderCreateSchema, OrderItemCreate, OrderStatusTransitionSchema


class TestOrderItemCreateTypes:
    def test_valid_item(self) -> None:
        item = OrderItemCreate(dish_id=uuid.uuid4(), quantity=2)
        assert item.quantity == 2

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=0)

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=-1)

    def test_quantity_over_100_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=101)

    def test_notes_max_length(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=1, notes="x" * 501)


class TestOrderCreateSchemaTypes:
    def test_valid_order(self) -> None:
        schema = OrderCreateSchema(
            table_number=5,
            items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}],
        )
        assert schema.table_number == 5
        assert len(schema.items) == 1

    def test_empty_items_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(items=[])

    def test_table_number_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                table_number=1000,
                items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}],
            )

    def test_table_number_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                table_number=0,
                items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}],
            )

    def test_no_table_number_valid(self) -> None:
        schema = OrderCreateSchema(
            items=[{"dish_id": str(uuid.uuid4()), "quantity": 3}],
        )
        assert schema.table_number is None


class TestOrderStatusTransitionTypes:
    def test_created_to_in_progress_allowed(self) -> None:
        OrderStatusTransitionSchema.validate_transition(
            OrderStatus.CREATED, OrderStatus.IN_PROGRESS
        )

    def test_created_to_closed_raises(self) -> None:
        with pytest.raises(ValueError):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CREATED, OrderStatus.CLOSED
            )

    def test_closed_is_terminal(self) -> None:
        with pytest.raises(ValueError):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CLOSED, OrderStatus.CANCELLED
            )

    def test_cancelled_is_terminal(self) -> None:
        with pytest.raises(ValueError):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CANCELLED, OrderStatus.CREATED
            )

    @pytest.mark.parametrize(
        "current,next_status",
        [
            (OrderStatus.CREATED, OrderStatus.IN_PROGRESS),
            (OrderStatus.CREATED, OrderStatus.CANCELLED),
            (OrderStatus.IN_PROGRESS, OrderStatus.READY),
            (OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED),
            (OrderStatus.READY, OrderStatus.CLOSED),
        ],
    )
    def test_all_valid_transitions(
        self, current: OrderStatus, next_status: OrderStatus
    ) -> None:
        OrderStatusTransitionSchema.validate_transition(current, next_status)
