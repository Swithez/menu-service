"""
Type-driven tests for the permissions registry.

Ensures the static permission definitions are internally consistent.
No database or HTTP involved.
"""
import pytest

from app.permissions import (
    ALL_PERMISSIONS,
    ALL_CODES,
    ADMIN_PERMISSIONS,
    PERMISSION_GROUPS,
    PERMISSION_MAP,
    Permission,
)


class TestPermissionRegistry:
    def test_all_permissions_non_empty(self) -> None:
        assert len(ALL_PERMISSIONS) > 0

    def test_all_codes_unique(self) -> None:
        codes = [p.code for p in ALL_PERMISSIONS]
        assert len(codes) == len(set(codes)), "Duplicate permission codes found"

    def test_all_codes_set_matches_list(self) -> None:
        expected = {p.code for p in ALL_PERMISSIONS}
        assert ALL_CODES == expected

    def test_admin_permissions_is_all_codes(self) -> None:
        assert ADMIN_PERMISSIONS == ALL_CODES

    def test_every_permission_has_non_empty_fields(self) -> None:
        for p in ALL_PERMISSIONS:
            assert p.code.strip(), f"Empty code: {p}"
            assert p.description.strip(), f"Empty description: {p}"
            assert p.group.strip(), f"Empty group: {p}"

    def test_codes_follow_colon_convention(self) -> None:
        """Codes must have at least one colon: domain:action or domain:resource:action."""
        for p in ALL_PERMISSIONS:
            assert ":" in p.code, f"Bad code format (no colon): {p.code}"

    def test_permission_groups_covers_all(self) -> None:
        grouped_codes: set[str] = set()
        for perms in PERMISSION_GROUPS.values():
            for p in perms:
                grouped_codes.add(p.code)
        assert grouped_codes == ALL_CODES

    def test_permission_map_keys_match_codes(self) -> None:
        assert set(PERMISSION_MAP.keys()) == ALL_CODES

    def test_permission_map_values_are_permission_objects(self) -> None:
        for code, perm in PERMISSION_MAP.items():
            assert isinstance(perm, Permission)
            assert perm.code == code

    def test_known_groups_present(self) -> None:
        groups = set(PERMISSION_GROUPS.keys())
        for expected in ("Меню", "Склад", "Заказы", "Пользователи"):
            assert expected in groups, f"Group '{expected}' missing"

    def test_role_permissions_in_users_group(self) -> None:
        users_perms = {p.code for p in PERMISSION_GROUPS.get("Пользователи", [])}
        assert "users:roles:manage" in users_perms
        assert "users:users:manage" in users_perms

    @pytest.mark.parametrize("code", [
        "menu:categories:read",
        "menu:dishes:write",
        "warehouse:products:read",
        "orders:create",
        "orders:close",
        "users:roles:manage",
        "users:users:manage",
    ])
    def test_expected_codes_exist(self, code: str) -> None:
        assert code in ALL_CODES, f"Expected permission '{code}' not found"
