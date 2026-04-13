from app.clients.base import BaseClient
from app.config import settings


class OrderClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.order_service_url)

    def list_orders(self, status: str | None = None, table_number: str | None = None) -> list[dict]:
        params = {}
        if status:
            params["status"] = status
        if table_number:
            params["table_number"] = table_number
        return self.get("/api/v1/orders/", **params) or []

    def get_order(self, order_id: str) -> dict:
        return self.get(f"/api/v1/orders/{order_id}")

    def create_order(self, data: dict) -> dict:
        return self.post("/api/v1/orders/", json=data)

    def take(self, order_id: str) -> dict:
        return self.post(f"/api/v1/orders/{order_id}/take")

    def ready(self, order_id: str) -> dict:
        return self.post(f"/api/v1/orders/{order_id}/ready")

    def close(self, order_id: str) -> dict:
        return self.post(f"/api/v1/orders/{order_id}/close")

    def cancel(self, order_id: str) -> dict:
        return self.post(f"/api/v1/orders/{order_id}/cancel")

    def delete_order(self, order_id: str) -> None:
        self.delete(f"/api/v1/orders/{order_id}")
