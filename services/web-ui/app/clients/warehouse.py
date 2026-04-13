from app.clients.base import BaseClient
from app.config import settings


class WarehouseClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.warehouse_service_url)

    def list_products(self, low_stock_only: bool = False) -> list[dict]:
        return self.get("/api/v1/products/", low_stock_only=low_stock_only) or []

    def get_product(self, product_id: str) -> dict:
        return self.get(f"/api/v1/products/{product_id}")

    def create_product(self, data: dict) -> dict:
        return self.post("/api/v1/products/", json=data)

    def update_product(self, product_id: str, data: dict) -> dict:
        return self.patch(f"/api/v1/products/{product_id}", json=data)

    def adjust_stock(self, product_id: str, data: dict) -> dict:
        return self.post(f"/api/v1/products/{product_id}/stock", json=data)

    def get_movements(self, product_id: str) -> list[dict]:
        return self.get(f"/api/v1/products/{product_id}/movements") or []

    def delete_product(self, product_id: str) -> None:
        self.delete(f"/api/v1/products/{product_id}")
