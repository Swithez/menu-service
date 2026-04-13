from typing import Any

import httpx


class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 0) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BaseClient:
    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = 8.0

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _handle(self, resp: httpx.Response) -> Any:
        if resp.status_code == 401:
            raise ServiceError("Unauthorized", 401)
        if resp.status_code == 403:
            detail = ""
            try:
                detail = resp.json().get("detail", "")
            except Exception:
                pass
            raise ServiceError(detail or "Forbidden", 403)
        if resp.status_code == 404:
            raise ServiceError("Not found", 404)
        if resp.status_code == 409:
            detail = resp.json().get("detail", "Conflict")
            raise ServiceError(detail, 409)
        if resp.status_code == 422:
            errors = resp.json().get("detail", [])
            if isinstance(errors, list):
                msg = "; ".join(
                    e.get("msg", str(e)) for e in errors
                )
            else:
                msg = str(errors)
            raise ServiceError(msg, 422)
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("detail", "")
            except Exception:
                pass
            raise ServiceError(detail or f"Error {resp.status_code}", resp.status_code)
        if resp.status_code == 204:
            return None
        return resp.json()

    def get(self, path: str, headers: dict | None = None, **params: Any) -> Any:
        try:
            r = httpx.get(
                self._url(path),
                params=params or None,
                headers=headers,
                timeout=self._timeout,
            )
            return self._handle(r)
        except httpx.RequestError as exc:
            raise ServiceError(f"Service unavailable: {exc}", 503)

    def post(self, path: str, json: Any = None, headers: dict | None = None) -> Any:
        try:
            r = httpx.post(
                self._url(path), json=json, headers=headers, timeout=self._timeout
            )
            return self._handle(r)
        except httpx.RequestError as exc:
            raise ServiceError(f"Service unavailable: {exc}", 503)

    def put(self, path: str, json: Any = None, headers: dict | None = None) -> Any:
        try:
            r = httpx.put(
                self._url(path), json=json, headers=headers, timeout=self._timeout
            )
            return self._handle(r)
        except httpx.RequestError as exc:
            raise ServiceError(f"Service unavailable: {exc}", 503)

    def patch(self, path: str, json: Any = None, headers: dict | None = None) -> Any:
        try:
            r = httpx.patch(
                self._url(path), json=json, headers=headers, timeout=self._timeout
            )
            return self._handle(r)
        except httpx.RequestError as exc:
            raise ServiceError(f"Service unavailable: {exc}", 503)

    def delete(self, path: str, headers: dict | None = None) -> None:
        try:
            r = httpx.delete(self._url(path), headers=headers, timeout=self._timeout)
            self._handle(r)
        except httpx.RequestError as exc:
            raise ServiceError(f"Service unavailable: {exc}", 503)
