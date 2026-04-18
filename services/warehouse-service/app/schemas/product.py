import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.product import MovementType

VALID_UNITS = {"kg", "g", "l", "ml", "pcs", "tbsp", "tsp"}


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit: str = Field(..., description=f"Unit of measure. Allowed: {VALID_UNITS}")
    min_stock_level: Decimal = Field(Decimal("0"), ge=0)
    cost_price: Decimal | None = Field(None, gt=0)

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Product name must not be blank")
        return stripped

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str:
        if v.lower() not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {VALID_UNITS}")
        return v.lower()


class ProductCreate(ProductBase):
    initial_stock: Decimal = Field(Decimal("0"), ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    unit: str | None = None
    calories_per_unit: Decimal | None = Field(None, ge=0)
    min_stock_level: Decimal | None = Field(None, ge=0)
    cost_price: Decimal | None = Field(None, gt=0)

    @model_validator(mode="after")
    def at_least_one(self) -> "ProductUpdate":
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field is required")
        return self

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str | None) -> str | None:
        if v is not None and v.lower() not in VALID_UNITS:
            raise ValueError(f"Unit must be one of: {VALID_UNITS}")
        return v.lower() if v else v


class StockAdjust(BaseModel):
    """Adjust stock level (incoming delivery or write-off)."""

    quantity: Decimal = Field(..., description="Positive = add, negative = remove")
    movement_type: MovementType
    reason: str | None = Field(None, max_length=500)
    order_id: uuid.UUID | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_nonzero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Quantity must not be zero")
        return v

    @model_validator(mode="after")
    def outgoing_must_have_reason_or_order(self) -> "StockAdjust":
        if self.movement_type in (MovementType.OUTGOING, MovementType.WRITE_OFF):
            if not self.reason and not self.order_id:
                raise ValueError("Outgoing / write-off movements require reason or order_id")
        return self


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    movement_type: MovementType
    reason: str | None
    order_id: uuid.UUID | None
    created_at: datetime


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_stock: Decimal
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime
