"""
Type-driven tests for warehouse-service schemas.
Validates constraints and type coercion before any DB interaction.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.product import MovementType
from app.schemas.product import ProductCreate, ProductUpdate, StockAdjust


class TestProductCreateTypes:
    def test_valid_product(self) -> None:
        p = ProductCreate(name="Flour", unit="kg")
        assert p.name == "Flour"
        assert p.unit == "kg"
        assert p.initial_stock == Decimal("0")

    def test_unit_case_insensitive(self) -> None:
        p = ProductCreate(name="Milk", unit="L")
        assert p.unit == "l"

    def test_invalid_unit_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="X", unit="cups")

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="  ", unit="kg")

    def test_negative_min_stock_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Sugar", unit="kg", min_stock_level=Decimal("-1"))

    def test_zero_cost_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Oil", unit="l", cost_price=Decimal("0"))

    def test_initial_stock_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductCreate(name="Salt", unit="kg", initial_stock=Decimal("-5"))

    @pytest.mark.parametrize("unit", ["kg", "g", "l", "ml", "pcs", "tbsp", "tsp"])
    def test_all_valid_units(self, unit: str) -> None:
        p = ProductCreate(name=f"Product_{unit}", unit=unit)
        assert p.unit == unit


class TestProductUpdateTypes:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductUpdate()

    def test_name_only(self) -> None:
        u = ProductUpdate(name="New Name")
        assert u.name == "New Name"

    def test_invalid_unit_in_update_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductUpdate(unit="pounds")


class TestStockAdjustTypes:
    def test_valid_incoming(self) -> None:
        adj = StockAdjust(
            quantity=Decimal("10.5"),
            movement_type=MovementType.INCOMING,
        )
        assert adj.quantity == Decimal("10.5")

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValidationError):
            StockAdjust(quantity=Decimal("0"), movement_type=MovementType.INCOMING)

    def test_outgoing_without_reason_or_order_raises(self) -> None:
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
        import uuid
        adj = StockAdjust(
            quantity=Decimal("2"),
            movement_type=MovementType.WRITE_OFF,
            order_id=uuid.uuid4(),
        )
        assert adj.order_id is not None
