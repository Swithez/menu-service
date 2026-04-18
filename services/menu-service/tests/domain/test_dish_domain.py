"""
DDD: Domain tests for menu-service.

Tests dish and category schema rules in complete isolation —
no HTTP layer, no database.
"""
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.dish import DishCreate, DishUpdate, PriceUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate


# ── Dish schema ───────────────────────────────────────────────────────────────

class TestDishCreateDomain:
    """Domain rules: what makes a valid dish."""

    def test_minimal_valid_dish(self) -> None:
        dish = DishCreate(name="Borscht", price=Decimal("120.00"))
        assert dish.name == "Borscht"
        assert dish.price == Decimal("120.00")
        assert dish.is_available is True
        assert dish.category_id is None

    def test_name_is_stripped(self) -> None:
        dish = DishCreate(name="  Soup  ", price=Decimal("100.00"))
        assert dish.name == "Soup"

    def test_blank_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="   ", price=Decimal("100.00"))

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="", price=Decimal("100.00"))

    def test_zero_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="Free Dish", price=Decimal("0"))

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="X", price=Decimal("-50"))

    def test_with_category(self) -> None:
        cat_id = uuid.uuid4()
        dish = DishCreate(name="Steak", price=Decimal("800.00"), category_id=cat_id)
        assert dish.category_id == cat_id

    def test_unavailable_dish(self) -> None:
        dish = DishCreate(name="Seasonal", price=Decimal("300.00"), is_available=False)
        assert dish.is_available is False

    def test_name_max_length_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="x" * 256, price=Decimal("100.00"))


class TestDishUpdateDomain:
    """Domain rules: what makes a valid dish update."""

    def test_update_availability(self) -> None:
        update = DishUpdate(is_available=False)
        assert update.is_available is False

    def test_update_name(self) -> None:
        update = DishUpdate(name="New Name")
        assert update.name == "New Name"

    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishUpdate()

    def test_update_with_none_values_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishUpdate(name=None, description=None)


class TestPriceUpdateDomain:
    """Domain rules for standalone price updates."""

    def test_valid_price(self) -> None:
        pu = PriceUpdate(price=Decimal("199.99"))
        assert pu.price == Decimal("199.99")

    def test_zero_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("0"))

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("-1"))


# ── Category schema ───────────────────────────────────────────────────────────

class TestCategoryDomain:
    """Domain rules for categories."""

    def test_valid_category(self) -> None:
        cat = CategoryCreate(name="Soups")
        assert cat.name == "Soups"
        assert cat.is_active is True

    def test_name_stripped(self) -> None:
        cat = CategoryCreate(name="  Hot Dishes  ")
        assert cat.name == "Hot Dishes"

    def test_blank_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="  ")

    def test_inactive_category(self) -> None:
        cat = CategoryCreate(name="Archived", is_active=False)
        assert cat.is_active is False

    def test_update_name(self) -> None:
        update = CategoryUpdate(name="Updated Name")
        assert update.name == "Updated Name"

    def test_update_blank_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(name="   ")
