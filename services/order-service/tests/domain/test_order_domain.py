"""
Доменные тесты order-service.

Модели и бизнес-правила в изоляции — без HTTP и внешних сервисов.

  - TestOrderAggregate            — инварианты модели Order (нужен app ctx для SQLAlchemy)
  - TestOrderStatusTransitions    — правила переходов статусов
  - TestOrderCreateSchema         — валидация схемы создания заказа
  - TestOrderItemSchema           — валидация схемы позиции заказа
"""
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreateSchema, OrderItemCreate, OrderStatusTransitionSchema


# ── Фикстуры ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def flask_app():
    """Минимальное Flask-приложение на SQLite в памяти — нужно для инстанциирования моделей."""
    from app.main import create_app
    from app.extensions import db as _db

    app = create_app(testing=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def app_ctx(flask_app):
    with flask_app.app_context():
        yield


# ── Вспомогательные функции ──────────────────────────────────────────────────

def _make_order(**kwargs) -> Order:
    return Order(status=OrderStatus.CREATED, **kwargs)


def _make_item(price: str = "100.00", qty: int = 1) -> OrderItem:
    return OrderItem(
        dish_id=uuid.uuid4(),
        dish_name="Test Dish",
        quantity=qty,
        price_at_order=Decimal(price),
    )


# ── Агрегат Order ────────────────────────────────────────────────────────────

class TestOrderAggregate:
    """Инварианты агрегата Order."""

    def test_total_zero_for_empty_order(self, app_ctx) -> None:
        order = _make_order()
        order.recalculate_total()
        assert order.total_amount == 0

    def test_total_single_item(self, app_ctx) -> None:
        order = _make_order()
        order.items.append(_make_item("150.00", qty=2))
        order.recalculate_total()
        assert order.total_amount == Decimal("300.00")

    def test_total_multiple_items(self, app_ctx) -> None:
        order = _make_order()
        order.items.append(_make_item("100.00", qty=3))  # 300.00
        order.items.append(_make_item("50.00", qty=2))   # 100.00
        order.recalculate_total()
        assert order.total_amount == Decimal("400.00")

    def test_total_recalculates_on_quantity_change(self, app_ctx) -> None:
        order = _make_order()
        item = _make_item("200.00", qty=1)
        order.items.append(item)
        order.recalculate_total()
        assert order.total_amount == Decimal("200.00")
        item.quantity = 3
        order.recalculate_total()
        assert order.total_amount == Decimal("600.00")

    def test_new_order_default_status(self, app_ctx) -> None:
        order = _make_order()
        assert order.status == OrderStatus.CREATED


# ── Правила переходов статусов (без БД) ──────────────────────────────────────

class TestOrderStatusTransitions:
    """Допустимые переходы состояний."""

    @pytest.mark.parametrize("current,nxt", [
        (OrderStatus.CREATED,     OrderStatus.IN_PROGRESS),
        (OrderStatus.CREATED,     OrderStatus.CANCELLED),
        (OrderStatus.IN_PROGRESS, OrderStatus.READY),
        (OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED),
        (OrderStatus.READY,       OrderStatus.CLOSED),
    ])
    def test_valid_transitions_pass(self, current: OrderStatus, nxt: OrderStatus) -> None:
        OrderStatusTransitionSchema.validate_transition(current, nxt)  # не должно выбрасывать исключение

    @pytest.mark.parametrize("current,nxt", [
        (OrderStatus.CREATED,     OrderStatus.READY),
        (OrderStatus.CREATED,     OrderStatus.CLOSED),
        (OrderStatus.IN_PROGRESS, OrderStatus.CREATED),
        (OrderStatus.READY,       OrderStatus.IN_PROGRESS),
        (OrderStatus.CLOSED,      OrderStatus.READY),
        (OrderStatus.CLOSED,      OrderStatus.CANCELLED),
        (OrderStatus.CANCELLED,   OrderStatus.CREATED),
        (OrderStatus.CANCELLED,   OrderStatus.IN_PROGRESS),
    ])
    def test_invalid_transitions_raise(self, current: OrderStatus, nxt: OrderStatus) -> None:
        with pytest.raises(ValueError):
            OrderStatusTransitionSchema.validate_transition(current, nxt)

    def test_closed_is_terminal(self) -> None:
        assert len(OrderStatusTransitionSchema.ALLOWED_TRANSITIONS[OrderStatus.CLOSED]) == 0

    def test_cancelled_is_terminal(self) -> None:
        assert len(OrderStatusTransitionSchema.ALLOWED_TRANSITIONS[OrderStatus.CANCELLED]) == 0


# ── OrderCreateSchema (чистый Pydantic) ──────────────────────────────────────

class TestOrderCreateSchema:
    """Правила схемы создания заказа."""

    def test_minimal_valid_order(self) -> None:
        schema = OrderCreateSchema(items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}])
        assert schema.table_number is None
        assert len(schema.items) == 1

    def test_all_fields(self) -> None:
        schema = OrderCreateSchema(
            table_number=5,
            customer_name="Alice",
            notes="No onions",
            items=[{"dish_id": str(uuid.uuid4()), "quantity": 2}],
        )
        assert schema.table_number == 5
        assert schema.customer_name == "Alice"

    def test_empty_items_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(items=[])

    def test_missing_items_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(table_number=1)  # type: ignore[call-arg]

    def test_table_number_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                table_number=0, items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}]
            )

    def test_table_number_over_999_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderCreateSchema(
                table_number=1000, items=[{"dish_id": str(uuid.uuid4()), "quantity": 1}]
            )


# ── OrderItemCreate (чистый Pydantic) ────────────────────────────────────────

class TestOrderItemSchema:
    """Правила схемы позиции заказа."""

    def test_valid_item(self) -> None:
        item = OrderItemCreate(dish_id=uuid.uuid4(), quantity=2)
        assert item.quantity == 2

    def test_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=0)

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=-1)

    def test_quantity_over_100_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=101)

    def test_notes_max_500_chars(self) -> None:
        with pytest.raises(ValidationError):
            OrderItemCreate(dish_id=uuid.uuid4(), quantity=1, notes="x" * 501)

    def test_notes_optional(self) -> None:
        item = OrderItemCreate(dish_id=uuid.uuid4(), quantity=1)
        assert item.notes is None


# ── Сообщения об ошибках переходов ───────────────────────────────────────────

class TestOrderTransitionMessages:
    """Ошибки переходов статусов выдаются на русском."""

    def test_terminal_state_error_mentions_final_state(self) -> None:
        with pytest.raises(ValueError, match="финальное состояние"):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CLOSED, OrderStatus.CANCELLED
            )

    def test_cancelled_state_also_terminal(self) -> None:
        with pytest.raises(ValueError, match="финальное состояние"):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CANCELLED, OrderStatus.CREATED
            )

    def test_invalid_transition_lists_allowed_in_russian(self) -> None:
        with pytest.raises(ValueError, match="Доступные переходы"):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.CREATED, OrderStatus.CLOSED
            )

    def test_error_contains_source_status_in_russian(self) -> None:
        with pytest.raises(ValueError, match="Нельзя перевести"):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.READY, OrderStatus.IN_PROGRESS
            )

    def test_error_contains_ready_status_name(self) -> None:
        with pytest.raises(ValueError, match="Готово к выдаче"):
            OrderStatusTransitionSchema.validate_transition(
                OrderStatus.READY, OrderStatus.CREATED
            )
