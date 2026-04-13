"""
Type-driven tests for CategoryCreate / CategoryUpdate / CategoryResponse.

Validates that Pydantic schemas enforce correct types and constraints
BEFORE any database or HTTP layer is involved.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


# ─── CategoryCreate ────────────────────────────────────────────────────────────

class TestCategoryCreateTypes:
    def test_valid_minimal(self) -> None:
        cat = CategoryCreate(name="Salads")
        assert cat.name == "Salads"
        assert cat.is_active is True
        assert cat.description is None

    def test_name_is_stripped(self) -> None:
        cat = CategoryCreate(name="  Soups  ")
        assert cat.name == "Soups"

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            CategoryCreate(name="x" * 256)
        assert "name" in str(exc.value)

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="   ")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(name="")

    def test_description_max_length(self) -> None:
        # 2001 chars should fail
        with pytest.raises(ValidationError):
            CategoryCreate(name="Valid", description="x" * 2001)

    def test_is_active_defaults_true(self) -> None:
        cat = CategoryCreate(name="Drinks")
        assert cat.is_active is True

    def test_is_active_false(self) -> None:
        cat = CategoryCreate(name="Old", is_active=False)
        assert cat.is_active is False

    @pytest.mark.parametrize("name", ["Burgers", "Пицца", "Starters & Soups", "Category-1"])
    def test_valid_names(self, name: str) -> None:
        cat = CategoryCreate(name=name)
        assert cat.name == name


# ─── CategoryUpdate ────────────────────────────────────────────────────────────

class TestCategoryUpdateTypes:
    def test_all_none_is_valid(self) -> None:
        # Update allows all-None (PATCH semantics — field-level nullability)
        upd = CategoryUpdate()
        assert upd.name is None
        assert upd.is_active is None

    def test_partial_update_name_only(self) -> None:
        upd = CategoryUpdate(name="New Name")
        assert upd.name == "New Name"
        assert upd.is_active is None

    def test_blank_name_in_update_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(name="   ")

    def test_name_is_stripped_in_update(self) -> None:
        upd = CategoryUpdate(name="  Trimmed  ")
        assert upd.name == "Trimmed"


# ─── CategoryResponse ──────────────────────────────────────────────────────────

class TestCategoryResponseTypes:
    def test_from_attributes(self) -> None:
        import uuid
        from datetime import datetime, timezone

        class FakeCategory:
            id = uuid.uuid4()
            name = "Pasta"
            description = "Italian pasta dishes"
            is_active = True
            created_at = datetime.now(tz=timezone.utc)
            updated_at = datetime.now(tz=timezone.utc)

        resp = CategoryResponse.model_validate(FakeCategory())
        assert resp.name == "Pasta"
        assert isinstance(resp.id, uuid.UUID)
