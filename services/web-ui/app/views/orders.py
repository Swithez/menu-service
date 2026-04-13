from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.clients.base import ServiceError
from app.clients.menu import MenuClient
from app.clients.order import OrderClient

bp = Blueprint("orders", __name__, url_prefix="/orders")

STATUS_LABELS = {
    "CREATED": ("primary", "bi-clock"),
    "IN_PROGRESS": ("warning", "bi-fire"),
    "READY": ("info", "bi-check-circle"),
    "CLOSED": ("success", "bi-bag-check"),
    "CANCELLED": ("secondary", "bi-x-circle"),
}


def _client() -> OrderClient:
    return OrderClient()


@bp.get("/")
def order_list():
    status_filter = request.args.get("status") or None
    table_filter = request.args.get("table_number") or None
    try:
        order_data = _client().list_orders(status=status_filter, table_number=table_filter)
    except ServiceError as e:
        flash(e.message, "danger")
        order_data = []
    return render_template(
        "orders/list.html",
        orders=order_data,
        status_filter=status_filter,
        table_filter=table_filter,
        STATUS_LABELS=STATUS_LABELS,
        all_statuses=list(STATUS_LABELS.keys()),
    )


@bp.get("/new")
def new_order():
    try:
        dishes = MenuClient().list_dishes(available_only=True)
    except ServiceError as e:
        flash(f"Cannot load menu: {e.message}", "danger")
        dishes = []
    return render_template("orders/create.html", dishes=dishes)


@bp.post("/new")
def create_order():
    table_raw = request.form.get("table_number", "").strip()
    customer = request.form.get("customer_name", "").strip() or None
    notes = request.form.get("notes", "").strip() or None

    dish_ids = request.form.getlist("dish_id[]")
    quantities = request.form.getlist("quantity[]")
    item_notes = request.form.getlist("item_notes[]")

    items = []
    for i, did in enumerate(dish_ids):
        if not did:
            continue
        qty_raw = quantities[i] if i < len(quantities) else "1"
        try:
            qty = int(qty_raw)
        except ValueError:
            qty = 1
        item: dict = {"dish_id": did, "quantity": max(1, qty)}
        if i < len(item_notes) and item_notes[i].strip():
            item["notes"] = item_notes[i].strip()
        items.append(item)

    if not items:
        flash("Add at least one dish to the order.", "danger")
        return redirect(url_for("orders.new_order"))

    payload: dict = {"items": items}
    if table_raw:
        try:
            payload["table_number"] = int(table_raw)
        except ValueError:
            pass
    if customer:
        payload["customer_name"] = customer
    if notes:
        payload["notes"] = notes

    try:
        order = _client().create_order(payload)
        flash("Order created successfully.", "success")
        return redirect(url_for("orders.order_detail", order_id=order["id"]))
    except ServiceError as e:
        flash(e.message, "danger")
        return redirect(url_for("orders.new_order"))


@bp.get("/<order_id>")
def order_detail(order_id: str):
    try:
        order = _client().get_order(order_id)
    except ServiceError as e:
        flash(e.message, "danger")
        return redirect(url_for("orders.order_list"))
    return render_template(
        "orders/detail.html",
        order=order,
        STATUS_LABELS=STATUS_LABELS,
    )


@bp.post("/<order_id>/take")
def take_order(order_id: str):
    try:
        _client().take(order_id)
        flash("Order taken into work.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("orders.order_detail", order_id=order_id))


@bp.post("/<order_id>/ready")
def mark_ready(order_id: str):
    try:
        _client().ready(order_id)
        flash("Order marked as ready.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("orders.order_detail", order_id=order_id))


@bp.post("/<order_id>/close")
def close_order(order_id: str):
    try:
        _client().close(order_id)
        flash("Order closed successfully.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("orders.order_detail", order_id=order_id))


@bp.post("/<order_id>/cancel")
def cancel_order(order_id: str):
    try:
        _client().cancel(order_id)
        flash("Order cancelled.", "warning")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("orders.order_detail", order_id=order_id))


@bp.post("/<order_id>/delete")
def delete_order(order_id: str):
    try:
        _client().delete_order(order_id)
        flash("Order deleted.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("orders.order_list"))
