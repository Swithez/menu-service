"""
Order API endpoints — full lifecycle:
  POST   /api/v1/orders/                        Create order
  GET    /api/v1/orders/                        List orders (filterable)
  GET    /api/v1/orders/<id>                    Get order
  PATCH  /api/v1/orders/<id>/status             Transition status
  POST   /api/v1/orders/<id>/take               Shortcut: CREATED -> IN_PROGRESS
  POST   /api/v1/orders/<id>/ready              Shortcut: IN_PROGRESS -> READY
  POST   /api/v1/orders/<id>/close              Shortcut: READY -> CLOSED
  POST   /api/v1/orders/<id>/cancel             Cancel order
  DELETE /api/v1/orders/<id>                    Delete (admin only)
"""
import uuid
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.extensions import db
from app.models.order import OrderStatus
from app.repositories.order import OrderRepository
from app.schemas.order import (
    OrderCreateSchema,
    OrderResponseSchema,
    OrderStatusTransitionSchema,
)
from app.services.order import OrderService

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


def _get_service() -> OrderService:
    return OrderService(OrderRepository())


def _serialize(order) -> dict:  # type: ignore[no-untyped-def]
    return OrderResponseSchema.model_validate(order).model_dump(mode="json")


@orders_bp.post("/")
def create_order():  # type: ignore[no-untyped-def]
    try:
        data = OrderCreateSchema.model_validate(request.get_json(force=True) or {})
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), HTTPStatus.UNPROCESSABLE_ENTITY

    service = _get_service()
    order = service.create_order(data)
    db.session.commit()
    return jsonify(_serialize(order)), HTTPStatus.CREATED


@orders_bp.get("/")
def list_orders():  # type: ignore[no-untyped-def]
    status_raw = request.args.get("status")
    status: OrderStatus | None = None
    if status_raw:
        try:
            status = OrderStatus(status_raw.upper())
        except ValueError:
            return jsonify({"detail": f"Invalid status: {status_raw}"}), HTTPStatus.BAD_REQUEST

    table_raw = request.args.get("table_number")
    table_number = int(table_raw) if table_raw else None
    limit = min(int(request.args.get("limit", 100)), 200)
    offset = int(request.args.get("offset", 0))

    service = _get_service()
    orders = service.list_orders(status=status, table_number=table_number, limit=limit, offset=offset)
    return jsonify([_serialize(o) for o in orders])


@orders_bp.get("/<uuid:order_id>")
def get_order(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    return jsonify(_serialize(service.get_order(order_id)))


@orders_bp.patch("/<uuid:order_id>/status")
def transition_status(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    body = request.get_json(force=True) or {}
    try:
        payload = OrderStatusTransitionSchema.model_validate(body)
    except ValidationError as exc:
        return jsonify({"detail": exc.errors()}), HTTPStatus.UNPROCESSABLE_ENTITY

    service = _get_service()
    order = service.transition_status(order_id, payload.status)
    db.session.commit()
    return jsonify(_serialize(order))


@orders_bp.post("/<uuid:order_id>/take")
def take_order(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    order = service.transition_status(order_id, OrderStatus.IN_PROGRESS)
    db.session.commit()
    return jsonify(_serialize(order))


@orders_bp.post("/<uuid:order_id>/ready")
def mark_ready(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    order = service.transition_status(order_id, OrderStatus.READY)
    db.session.commit()
    return jsonify(_serialize(order))


@orders_bp.post("/<uuid:order_id>/close")
def close_order(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    order = service.transition_status(order_id, OrderStatus.CLOSED)
    # commit already called in service for CLOSED (before warehouse notify)
    if db.session.is_active:
        db.session.commit()
    return jsonify(_serialize(order))


@orders_bp.post("/<uuid:order_id>/cancel")
def cancel_order(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    order = service.cancel_order(order_id)
    db.session.commit()
    return jsonify(_serialize(order))


@orders_bp.delete("/<uuid:order_id>")
def delete_order(order_id: uuid.UUID):  # type: ignore[no-untyped-def]
    service = _get_service()
    order = service.get_order(order_id)
    OrderRepository().delete(order)
    db.session.commit()
    return "", HTTPStatus.NO_CONTENT
