"""
Central permissions registry.
Every permission the system knows about is defined here.
New permissions require a code change + re-seed — intentionally.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    code: str
    description: str
    group: str


# ── All permissions ────────────────────────────────────────────────────────────
ALL_PERMISSIONS: list[Permission] = [
    # Menu — categories
    Permission("menu:categories:read",           "Просмотр категорий",           "Меню"),
    Permission("menu:categories:write",          "Управление категориями",        "Меню"),
    # Menu — dishes
    Permission("menu:dishes:read",               "Просмотр блюд",                "Меню"),
    Permission("menu:dishes:write",              "Управление блюдами",            "Меню"),
    Permission("menu:dishes:price:write",        "Изменение цен на блюда",        "Меню"),
    Permission("menu:dishes:price_history:read", "Просмотр истории цен",          "Меню"),
    # Warehouse
    Permission("warehouse:products:read",        "Просмотр продуктов склада",     "Склад"),
    Permission("warehouse:products:write",       "Управление продуктами склада",  "Склад"),
    Permission("warehouse:stock:incoming",       "Приёмка товара",                "Склад"),
    Permission("warehouse:stock:outgoing",       "Списание расхода",              "Склад"),
    Permission("warehouse:stock:write_off",      "Ручное списание (потери)",      "Склад"),
    Permission("warehouse:cost_price:read",      "Просмотр себестоимости",        "Склад"),
    # Orders
    Permission("orders:create",                  "Создание заказов",              "Заказы"),
    Permission("orders:read:own",                "Просмотр своих заказов",        "Заказы"),
    Permission("orders:read:all",                "Просмотр всех заказов",         "Заказы"),
    Permission("orders:take",                    "Взять заказ в работу",          "Заказы"),
    Permission("orders:ready",                   "Отметить заказ готовым",        "Заказы"),
    Permission("orders:close",                   "Закрыть заказ (принять оплату)","Заказы"),
    Permission("orders:cancel:own",              "Отменить свой заказ",           "Заказы"),
    Permission("orders:cancel:any",              "Отменить любой заказ",          "Заказы"),
    Permission("orders:delete",                  "Удалить заказ",                 "Заказы"),
    # Users & roles — deliberately last (most sensitive)
    Permission("users:read",                     "Просмотр пользователей",        "Пользователи"),
    Permission("users:users:manage",             "Управление пользователями",     "Пользователи"),
    Permission("users:roles:manage",             "Управление ролями",             "Пользователи"),
]

ALL_CODES: set[str] = {p.code for p in ALL_PERMISSIONS}

ADMIN_PERMISSIONS: set[str] = ALL_CODES   # admin gets everything

PERMISSION_GROUPS: dict[str, list[Permission]] = {}
for _p in ALL_PERMISSIONS:
    PERMISSION_GROUPS.setdefault(_p.group, []).append(_p)

# Quick lookup by code
PERMISSION_MAP: dict[str, Permission] = {p.code: p for p in ALL_PERMISSIONS}
