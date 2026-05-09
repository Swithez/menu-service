"""
Фикстуры order-service.
SQLite в памяти, межсервисные HTTP-запросы заглушены.
"""
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.main import create_app
from app.extensions import db as _db


FAKE_DISH = {
    "id": str(uuid.uuid4()),
    "name": "Borscht",
    "price": "150.00",
    "is_available": True,
    "category_id": None,
    "description": None,
    "image_url": None,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


@pytest.fixture(scope="session")
def app():
    flask_app = create_app(testing=True)
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def rollback_after_test(app):
    """Каждый тест — в своей транзакции."""
    with app.app_context():
        _db.session.begin_nested()
        yield
        _db.session.rollback()


@pytest.fixture()
def mock_menu_service():
    """Заглушка httpx.get: возвращает блюдо или пустые ингредиенты по URL."""
    def _side_effect(url: str, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.status_code = 200
        if "/ingredients" in url:
            resp.json.return_value = []
        else:
            resp.json.return_value = FAKE_DISH
        return resp

    with patch("httpx.get", side_effect=_side_effect) as mock:
        yield mock, FAKE_DISH
