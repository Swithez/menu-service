"""
Доменные тесты menu-service.

Схемы блюд и категорий — без HTTP и базы данных.
"""
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.dish import DishCreate, DishIngredientCreate, DishUpdate, PriceUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate


# ── Схема блюда ──────────────────────────────────────────────────────────────

class TestDishCreateDomain:
    """Правила создания блюда."""

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
    """Правила обновления блюда."""

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
    """Правила обновления цены."""

    def test_valid_price(self) -> None:
        pu = PriceUpdate(price=Decimal("199.99"))
        assert pu.price == Decimal("199.99")

    def test_zero_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("0"))

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("-1"))


# ── Схема категории ──────────────────────────────────────────────────────────

class TestCategoryDomain:
    """Правила создания и обновления категории."""

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


# ── Схема ингредиента ────────────────────────────────────────────────────────

class TestDishIngredientDomain:
    """Правила схемы ингредиента блюда."""

    def test_valid_ingredient(self) -> None:
        ing = DishIngredientCreate(
            product_id=uuid.uuid4(),
            product_name="Chicken",
            quantity=Decimal("0.300"),
            unit="kg",
        )
        assert ing.product_name == "Chicken"
        assert ing.quantity == Decimal("0.300")
        assert ing.unit == "kg"

    def test_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="X", quantity=Decimal("0"), unit="kg"
            )

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="X", quantity=Decimal("-1"), unit="kg"
            )

    def test_empty_product_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="", quantity=Decimal("1"), unit="kg"
            )

    def test_empty_unit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="Chicken", quantity=Decimal("1"), unit=""
            )

    def test_product_name_max_length_enforced(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="x" * 256, quantity=Decimal("1"), unit="kg"
            )

    def test_unit_max_length_enforced(self) -> None:
        with pytest.raises(ValidationError):
            DishIngredientCreate(
                product_id=uuid.uuid4(), product_name="Salt", quantity=Decimal("1"),
                unit="x" * 51,
            )
