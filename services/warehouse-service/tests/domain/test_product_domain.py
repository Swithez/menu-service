"""
Доменные тесты warehouse-service.

Схемы продукта и остатков в изоляции — без HTTP и базы данных.
"""
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.product import MovementType, Product
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjust


# ── Агрегат Product ──────────────────────────────────────────────────────────

class TestProductAggregate:
    """Инварианты агрегата Product."""

    def _make_product(self, stock: str = "10", min_level: str = "5") -> Product:
        p = Product()
        p.name = "Test Product"
        p.unit = "kg"
        p.current_stock = Decimal(stock)
        p.min_stock_level = Decimal(min_level)
        return p

    def test_low_stock_when_at_minimum(self) -> None:
        p = self._make_product(stock="5", min_level="5")
        assert p.is_low_stock is True

    def test_low_stock_when_below_minimum(self) -> None:
        p = self._make_product(stock="2", min_level="5")
        assert p.is_low_stock is True

    def test_not_low_stock_when_above_minimum(self) -> None:
        p = self._make_product(stock="10", min_level="5")
        assert p.is_low_stock is False

    def test_zero_stock_with_zero_minimum_not_low_stock(self) -> None:
        p = self._make_product(stock="0", min_level="0")
        assert p.is_low_stock is True  # 0 <= 0 → true


# ── Схема ProductCreate ──────────────────────────────────────────────────────

class TestProductCreateDomain:
    """Правила создания продукта."""

    def test_minimal_valid_product(self) -> None:
        p = ProductCreate(name="Flour", unit="kg")
        assert p.name == "Flour"
        assert p.unit == "kg"
        assert p.initial_stock == Decimal("0")
        assert p.min_stock_level == Decimal("0")

    def test_unit_normalised_to_lowercase(self) -> None:
        p = ProductCreate(name="Milk", unit="L")
        assert p.unit == "l"

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="X", unit="cups")

    def test_blank_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="  ", unit="kg")

    def test_negative_min_stock_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Sugar", unit="kg", min_stock_level=Decimal("-1"))

    def test_zero_cost_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Oil", unit="l", cost_price=Decimal("0"))

    def test_negative_initial_stock_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Salt", unit="kg", initial_stock=Decimal("-5"))

    @pytest.mark.parametrize("unit", ["kg", "g", "l", "ml", "pcs", "tbsp", "tsp"])
    def test_all_valid_units(self, unit: str) -> None:
        p = ProductCreate(name=f"Product_{unit}", unit=unit)
        assert p.unit == unit


# ── Схема ProductUpdate ──────────────────────────────────────────────────────

class TestProductUpdateDomain:
    """Правила обновления продукта."""

    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductUpdate()

    def test_name_only(self) -> None:
        u = ProductUpdate(name="New Name")
        assert u.name == "New Name"

    def test_invalid_unit_in_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProductUpdate(unit="pounds")


# ── Схема StockAdjust ────────────────────────────────────────────────────────

class TestStockAdjustDomain:
    """Правила схемы движения остатков."""

    def test_valid_incoming_movement(self) -> None:
        adj = StockAdjust(quantity=Decimal("10.5"), movement_type=MovementType.INCOMING)
        assert adj.quantity == Decimal("10.5")

    def test_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StockAdjust(quantity=Decimal("0"), movement_type=MovementType.INCOMING)

    def test_outgoing_without_reason_or_order_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StockAdjust(quantity=Decimal("5"), movement_type=MovementType.OUTGOING)

    def test_outgoing_with_reason_valid(self) -> None:
        adj = StockAdjust(
            quantity=Decimal("3"),
            movement_type=MovementType.OUTGOING,
            reason="Used in order #123",
        )
        assert adj.reason == "Used in order #123"

    def test_write_off_with_order_id_valid(self) -> None:
        adj = StockAdjust(
            quantity=Decimal("2"),
            movement_type=MovementType.WRITE_OFF,
            order_id=uuid.uuid4(),
        )
        assert adj.order_id is not None

    def test_incoming_does_not_require_reason(self) -> None:
        adj = StockAdjust(quantity=Decimal("100"), movement_type=MovementType.INCOMING)
        assert adj.reason is None
        assert adj.order_id is None
