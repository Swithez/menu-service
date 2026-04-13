"""
Type-driven tests for DishCreate / DishUpdate / PriceUpdate schemas.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.dish import DishCreate, DishUpdate, PriceUpdate


class TestDishCreateTypes:
    def test_valid_minimal(self) -> None:
        dish = DishCreate(name="Borscht", price=Decimal("350.00"))
        assert dish.name == "Borscht"
        assert dish.price == Decimal("350.00")
        assert dish.is_available is True
        assert dish.calories is None

    def test_name_stripped(self) -> None:
        dish = DishCreate(name="  Shchi  ", price=Decimal("200"))
        assert dish.name == "Shchi"

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="   ", price=Decimal("100"))

    def test_zero_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="Free", price=Decimal("0"))

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="Negative", price=Decimal("-50"))

    def test_calories_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="X", price=Decimal("100"), calories=-1)

    def test_calories_max(self) -> None:
        with pytest.raises(ValidationError):
            DishCreate(name="X", price=Decimal("100"), calories=10001)

    def test_full_nutrition(self) -> None:
        dish = DishCreate(
            name="Steak",
            price=Decimal("1500.00"),
            calories=350,
            proteins=Decimal("28.5"),
            fats=Decimal("18.0"),
            carbohydrates=Decimal("0.0"),
            weight_grams=250,
        )
        assert dish.calories == 350
        assert dish.proteins == Decimal("28.5")
        assert dish.weight_grams == 250

    @pytest.mark.parametrize("price", ["100", "0.01", "99999.99"])
    def test_valid_price_strings(self, price: str) -> None:
        dish = DishCreate(name="Test", price=Decimal(price))
        assert dish.price > 0


class TestDishUpdateTypes:
    def test_empty_update_raises(self) -> None:
        with pytest.raises(ValidationError):
            DishUpdate()

    def test_single_field_update(self) -> None:
        upd = DishUpdate(is_available=False)
        assert upd.is_available is False

    def test_negative_calories_raises(self) -> None:
        with pytest.raises(ValidationError):
            DishUpdate(calories=-10)

    def test_name_only(self) -> None:
        upd = DishUpdate(name="New Name")
        assert upd.name == "New Name"


class TestPriceUpdateTypes:
    def test_valid_price(self) -> None:
        pu = PriceUpdate(price=Decimal("450.00"))
        assert pu.price == Decimal("450.00")

    def test_zero_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("0"))

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            PriceUpdate(price=Decimal("-1"))

    @pytest.mark.parametrize("price", [Decimal("0.01"), Decimal("9999.99"), Decimal("1")])
    def test_valid_prices(self, price: Decimal) -> None:
        pu = PriceUpdate(price=price)
        assert pu.price == price
