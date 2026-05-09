"""
Доменные тесты auth-service.

Только валидация Pydantic-схем — без БД и HTTP.
"""
import uuid

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
    PermissionSchema,
    RoleResponse,
    UserResponse,
)


# ── LoginRequest ──────────────────────────────────────────────────────────────

class TestLoginRequestTypes:
    def test_valid(self) -> None:
        req = LoginRequest(email="user@example.com", password="secret")
        assert req.email == "user@example.com"
        assert req.password == "secret"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="secret")

    def test_empty_password_raises(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest(email="user@example.com", password="")

    def test_email_domain_is_lowercased(self) -> None:
        # EmailStr нормализует только домен
        req = LoginRequest(email="User@EXAMPLE.COM", password="x")
        assert req.email.endswith("@example.com")


# ── RoleCreate ────────────────────────────────────────────────────────────────

class TestRoleCreateTypes:
    def test_valid_minimal(self) -> None:
        r = RoleCreate(name="manager")
        assert r.name == "manager"
        assert r.description is None
        assert r.permission_codes == []

    def test_name_is_stripped(self) -> None:
        r = RoleCreate(name="  manager  ")
        assert r.name == "manager"

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            RoleCreate(name="   ")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            RoleCreate(name="")

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            RoleCreate(name="x" * 101)

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            RoleCreate(name="ok", description="x" * 501)

    def test_permission_codes_list(self) -> None:
        r = RoleCreate(name="role", permission_codes=["menu:dishes:read"])
        assert "menu:dishes:read" in r.permission_codes

    def test_description_optional(self) -> None:
        r = RoleCreate(name="r", description="some text")
        assert r.description == "some text"


# ── RoleUpdate ────────────────────────────────────────────────────────────────

class TestRoleUpdateTypes:
    def test_at_least_one_field_required(self) -> None:
        with pytest.raises(ValidationError):
            RoleUpdate()

    def test_name_only(self) -> None:
        u = RoleUpdate(name="new-name")
        assert u.name == "new-name"

    def test_description_only(self) -> None:
        u = RoleUpdate(description="new desc")
        assert u.description == "new desc"

    def test_both_fields(self) -> None:
        u = RoleUpdate(name="n", description="d")
        assert u.name == "n"
        assert u.description == "d"

    def test_name_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            RoleUpdate(name="")


# ── UserCreate ────────────────────────────────────────────────────────────────

class TestUserCreateTypes:
    def test_valid_minimal(self) -> None:
        u = UserCreate(
            email="ivan@example.com",
            full_name="Ivan Ivanov",
            password="secure123",
        )
        assert u.email == "ivan@example.com"
        assert u.is_active is True
        assert u.role_id is None

    def test_email_domain_lowercased(self) -> None:
        u = UserCreate(email="Chef@EXAMPLE.COM", full_name="Chef", password="pass123")
        assert u.email.endswith("@example.com")

    def test_full_name_stripped(self) -> None:
        u = UserCreate(email="a@b.com", full_name="  John  ", password="pass123")
        assert u.full_name == "John"

    def test_password_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", full_name="X", password="12345")

    def test_password_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", full_name="X", password="x" * 129)

    def test_empty_full_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", full_name="", password="pass123")

    def test_full_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", full_name="x" * 256, password="pass123")

    def test_role_id_uuid(self) -> None:
        rid = uuid.uuid4()
        u = UserCreate(email="a@b.com", full_name="X", password="pass123", role_id=rid)
        assert u.role_id == rid

    @pytest.mark.parametrize("active", [True, False])
    def test_is_active_flag(self, active: bool) -> None:
        u = UserCreate(email="a@b.com", full_name="X", password="pass123", is_active=active)
        assert u.is_active is active


# ── UserUpdate ────────────────────────────────────────────────────────────────

class TestUserUpdateTypes:
    def test_all_none_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserUpdate()

    def test_password_only(self) -> None:
        u = UserUpdate(password="newpass1")
        assert u.password == "newpass1"

    def test_is_active_only(self) -> None:
        u = UserUpdate(is_active=False)
        assert u.is_active is False

    def test_full_name_only(self) -> None:
        u = UserUpdate(full_name="New Name")
        assert u.full_name == "New Name"

    def test_short_password_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserUpdate(password="12345")

    def test_full_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            UserUpdate(full_name="x" * 256)


# ── PermissionSchema ──────────────────────────────────────────────────────────

class TestPermissionSchemaTypes:
    def test_valid(self) -> None:
        p = PermissionSchema(code="menu:dishes:read", description="Просмотр блюд", group="Меню")
        assert p.code == "menu:dishes:read"
        assert p.group == "Меню"
