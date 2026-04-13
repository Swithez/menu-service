from app.clients.base import BaseClient
from app.config import settings


class AuthClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(settings.auth_service_url)

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        return self.post("/api/v1/auth/login", json={"email": email, "password": password})

    def get_me(self, token: str) -> dict:
        return self.get("/api/v1/auth/me", headers=self._auth(token))

    # ── Permissions ───────────────────────────────────────────────────────────

    def list_permissions_grouped(self, token: str) -> dict:
        return self.get("/api/v1/permissions/groups", headers=self._auth(token))

    # ── Roles ─────────────────────────────────────────────────────────────────

    def list_roles(self, token: str) -> list[dict]:
        return self.get("/api/v1/roles", headers=self._auth(token))

    def get_role(self, role_id: str, token: str) -> dict:
        return self.get(f"/api/v1/roles/{role_id}", headers=self._auth(token))

    def create_role(self, data: dict, token: str) -> dict:
        return self.post("/api/v1/roles", json=data, headers=self._auth(token))

    def update_role(self, role_id: str, data: dict, token: str) -> dict:
        return self.patch(f"/api/v1/roles/{role_id}", json=data, headers=self._auth(token))

    def set_role_permissions(self, role_id: str, codes: list[str], token: str) -> dict:
        return self.put(
            f"/api/v1/roles/{role_id}/permissions", json=codes, headers=self._auth(token)
        )

    def delete_role(self, role_id: str, token: str) -> None:
        self.delete(f"/api/v1/roles/{role_id}", headers=self._auth(token))

    # ── Users ─────────────────────────────────────────────────────────────────

    def list_users(self, token: str) -> list[dict]:
        return self.get("/api/v1/users", headers=self._auth(token))

    def get_user(self, user_id: str, token: str) -> dict:
        return self.get(f"/api/v1/users/{user_id}", headers=self._auth(token))

    def create_user(self, data: dict, token: str) -> dict:
        return self.post("/api/v1/users", json=data, headers=self._auth(token))

    def update_user(self, user_id: str, data: dict, token: str) -> dict:
        return self.patch(f"/api/v1/users/{user_id}", json=data, headers=self._auth(token))

    def delete_user(self, user_id: str, token: str) -> None:
        self.delete(f"/api/v1/users/{user_id}", headers=self._auth(token))
