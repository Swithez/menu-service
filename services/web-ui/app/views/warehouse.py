from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.clients.base import ServiceError
from app.clients.warehouse import WarehouseClient

bp = Blueprint("warehouse", __name__, url_prefix="/warehouse")


def _client() -> WarehouseClient:
    return WarehouseClient()


@bp.get("/products")
def products():
    low_only = request.args.get("low_stock") == "1"
    try:
        product_list = _client().list_products(low_stock_only=low_only)
    except ServiceError as e:
        flash(e.message, "danger")
        product_list = []
    return render_template("warehouse/products.html", products=product_list, low_only=low_only)


@bp.post("/products")
def create_product():
    def _v(key: str) -> str | None:
        v = request.form.get(key, "").strip()
        return v if v else None

    data: dict = {
        "name": request.form.get("name", "").strip(),
        "unit": request.form.get("unit", "").strip(),
    }
    if v := _v("min_stock_level"):
        data["min_stock_level"] = v
    if v := _v("cost_price"):
        data["cost_price"] = v
    if v := _v("initial_stock"):
        data["initial_stock"] = v
    try:
        _client().create_product(data)
        flash("Product created.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("warehouse.products"))


@bp.post("/products/<product_id>/update")
def update_product(product_id: str):
    def _v(key: str) -> str | None:
        v = request.form.get(key, "").strip()
        return v if v else None

    data: dict = {}
    if v := _v("name"):
        data["name"] = v
    if v := _v("unit"):
        data["unit"] = v
    if v := _v("min_stock_level"):
        data["min_stock_level"] = v
    if v := _v("cost_price"):
        data["cost_price"] = v

    if not data:
        flash("No fields to update.", "warning")
        return redirect(url_for("warehouse.products"))
    try:
        _client().update_product(product_id, data)
        flash("Product updated.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("warehouse.products"))


@bp.post("/products/<product_id>/stock")
def adjust_stock(product_id: str):
    qty = request.form.get("quantity", "").strip()
    movement_type = request.form.get("movement_type", "INCOMING")
    reason = request.form.get("reason", "").strip() or None
    data: dict = {
        "quantity": qty,
        "movement_type": movement_type,
    }
    if reason:
        data["reason"] = reason
    try:
        _client().adjust_stock(product_id, data)
        flash("Stock adjusted.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("warehouse.products"))


@bp.get("/products/<product_id>/movements")
def movements(product_id: str):
    client = _client()
    try:
        product = client.get_product(product_id)
        mvmts = client.get_movements(product_id)
    except ServiceError as e:
        flash(e.message, "danger")
        return redirect(url_for("warehouse.products"))
    return render_template("warehouse/movements.html", product=product, movements=mvmts)


@bp.post("/products/<product_id>/delete")
def delete_product(product_id: str):
    try:
        _client().delete_product(product_id)
        flash("Product deleted.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("warehouse.products"))
