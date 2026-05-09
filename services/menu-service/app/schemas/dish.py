import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Price in rubles")
    category_id: uuid.UUID | None = None
    is_available: bool = Field(True)
    image_url: str | None = None

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Dish name must not be blank")
        return stripped

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


class DishCreate(DishBase):
    pass


class DishUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    is_available: bool | None = None
    image_url: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "DishUpdate":
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided for update")
        return self


class PriceUpdate(BaseModel):
    price: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dish_id: uuid.UUID
    old_price: Decimal
    new_price: Decimal
    changed_at: datetime


class DishResponse(DishBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    ingredients: list["DishIngredientResponse"] = []


class DishIngredientCreate(BaseModel):
    product_id: uuid.UUID
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)


class DishIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dish_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: Decimal
    unit: str
