from typing import Any

from app.clients.base import BaseClient
from app.config import settings


class MenuClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.menu_service_url)

    # ── Categories ────────────────────────────────────────────────────
    def list_categories(self, active_only: bool = False) -> list[dict]:
        return self.get("/api/v1/categories/", active_only=active_only) or []

    def get_category(self, cat_id: str) -> dict:
        return self.get(f"/api/v1/categories/{cat_id}")

    def create_category(self, data: dict) -> dict:
        return self.post("/api/v1/categories/", json=data)

    def update_category(self, cat_id: str, data: dict) -> dict:
        return self.patch(f"/api/v1/categories/{cat_id}", json=data)

    def delete_category(self, cat_id: str) -> None:
        self.delete(f"/api/v1/categories/{cat_id}")

    # ── Dishes ────────────────────────────────────────────────────────
    def list_dishes(self, category_id: str | None = None, available_only: bool = False) -> list[dict]:
        params: dict[str, Any] = {}
        if category_id:
            params["category_id"] = category_id
        if available_only:
            params["available_only"] = True
        return self.get("/api/v1/dishes/", **params) or []

    def get_dish(self, dish_id: str) -> dict:
        return self.get(f"/api/v1/dishes/{dish_id}")

    def create_dish(self, data: dict) -> dict:
        return self.post("/api/v1/dishes/", json=data)

    def update_dish(self, dish_id: str, data: dict) -> dict:
        return self.patch(f"/api/v1/dishes/{dish_id}", json=data)

    def update_price(self, dish_id: str, price: str) -> dict:
        return self.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": price})

    def price_history(self, dish_id: str) -> list[dict]:
        return self.get(f"/api/v1/dishes/{dish_id}/price-history") or []

    def delete_dish(self, dish_id: str) -> None:
        self.delete(f"/api/v1/dishes/{dish_id}")
