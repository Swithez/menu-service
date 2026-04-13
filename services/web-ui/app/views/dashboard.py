from flask import Blueprint, render_template

from app.clients.base import ServiceError
from app.clients.menu import MenuClient
from app.clients.order import OrderClient
from app.clients.warehouse import WarehouseClient

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    menu = MenuClient()
    wh = WarehouseClient()
    orders = OrderClient()

    stats = {
        "dishes_total": 0,
        "dishes_available": 0,
        "categories": 0,
        "products_total": 0,
        "products_low_stock": 0,
        "orders_created": 0,
        "orders_in_progress": 0,
        "orders_ready": 0,
        "orders_closed": 0,
    }
    low_stock = []
    active_orders = []
    services_ok = True

    try:
        dishes = menu.list_dishes()
        stats["dishes_total"] = len(dishes)
        stats["dishes_available"] = sum(1 for d in dishes if d.get("is_available"))
        stats["categories"] = len(menu.list_categories())
    except ServiceError:
        services_ok = False

    try:
        products = wh.list_products()
        stats["products_total"] = len(products)
        low_stock = [p for p in products if p.get("is_low_stock")]
        stats["products_low_stock"] = len(low_stock)
    except ServiceError:
        services_ok = False

    try:
        for status in ("CREATED", "IN_PROGRESS", "READY", "CLOSED"):
            key = f"orders_{status.lower()}"
            lst = orders.list_orders(status=status)
            stats[key] = len(lst)
            if status in ("CREATED", "IN_PROGRESS", "READY"):
                active_orders.extend(lst)
        active_orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
        active_orders = active_orders[:10]
    except ServiceError:
        services_ok = False

    return render_template(
        "dashboard.html",
        stats=stats,
        low_stock=low_stock[:5],
        active_orders=active_orders,
        services_ok=services_ok,
    )
