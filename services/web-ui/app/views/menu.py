from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.clients.base import ServiceError
from app.clients.menu import MenuClient
from app.clients.warehouse import WarehouseClient

bp = Blueprint("menu", __name__, url_prefix="/menu")


def _client() -> MenuClient:
    return MenuClient()


# ─── Categories ────────────────────────────────────────────────────────────────

@bp.get("/categories")
def categories():
    try:
        cats = _client().list_categories()
    except ServiceError as e:
        flash(e.message, "danger")
        cats = []
    return render_template("menu/categories.html", categories=cats)


@bp.post("/categories")
def create_category():
    data = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }
    try:
        _client().create_category(data)
        flash("Category created.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.categories"))


@bp.post("/categories/<cat_id>/update")
def update_category(cat_id: str):
    data = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }
    try:
        _client().update_category(cat_id, data)
        flash("Category updated.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.categories"))


@bp.post("/categories/<cat_id>/delete")
def delete_category(cat_id: str):
    try:
        _client().delete_category(cat_id)
        flash("Category deleted.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.categories"))


@bp.post("/categories/<cat_id>/toggle")
def toggle_category(cat_id: str):
    try:
        c = _client().get_category(cat_id)
        _client().update_category(cat_id, {"is_active": not c["is_active"]})
        flash("Category status changed.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.categories"))


# ─── Dishes ────────────────────────────────────────────────────────────────────

@bp.get("/dishes")
def dishes():
    cat_filter = request.args.get("category_id") or None
    avail_only = request.args.get("available_only") == "1"
    client = _client()
    try:
        dish_list = client.list_dishes(category_id=cat_filter, available_only=avail_only)
        cat_list = client.list_categories()
    except ServiceError as e:
        flash(e.message, "danger")
        dish_list, cat_list = [], []

    # Build product stock map for availability check
    product_stock: dict[str, float] = {}
    try:
        for p in WarehouseClient().list_products():
            product_stock[p["id"]] = float(p["current_stock"])
    except ServiceError:
        pass

    # Annotate each dish with stock-based availability
    for dish in dish_list:
        ingredients = dish.get("ingredients") or []
        if not ingredients:
            dish["_stock_ok"] = None  # no recipe configured — no check
        else:
            ok = all(
                product_stock.get(ing["product_id"], 0) >= float(ing["quantity"])
                for ing in ingredients
            )
            dish["_stock_ok"] = ok

    return render_template(
        "menu/dishes.html",
        dishes=dish_list,
        categories=cat_list,
        cat_filter=cat_filter,
        avail_only=avail_only,
    )


@bp.post("/dishes")
def create_dish():
    def _dec(key: str) -> str | None:
        v = request.form.get(key, "").strip()
        return v if v else None

    data: dict = {
        "name": request.form.get("name", "").strip(),
        "price": request.form.get("price", "").strip(),
        "description": _dec("description"),
        "category_id": _dec("category_id"),
        "is_available": request.form.get("is_available") == "on",
        "image_url": _dec("image_url"),
    }
    try:
        _client().create_dish(data)
        flash("Dish created.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dishes"))


@bp.get("/dishes/<dish_id>")
def dish_detail(dish_id: str):
    client = _client()
    try:
        dish = client.get_dish(dish_id)
        history = client.price_history(dish_id)
        cats = client.list_categories()
        ingredients = client.get_ingredients(dish_id)
    except ServiceError as e:
        flash(e.message, "danger")
        return redirect(url_for("menu.dishes"))
    try:
        products = WarehouseClient().list_products()
    except ServiceError:
        products = []
    return render_template(
        "menu/dish_detail.html",
        dish=dish,
        history=history,
        categories=cats,
        ingredients=ingredients,
        products=products,
    )


@bp.post("/dishes/<dish_id>/update")
def update_dish(dish_id: str):
    def _dec(key: str) -> str | None:
        v = request.form.get(key, "").strip()
        return v if v else None

    data: dict = {}
    if n := _dec("name"):
        data["name"] = n
    if d := _dec("description"):
        data["description"] = d
    if c := _dec("category_id"):
        data["category_id"] = c
    data["is_available"] = request.form.get("is_available") == "on"
    if _dec("image_url"):
        data["image_url"] = _dec("image_url")
    try:
        _client().update_dish(dish_id, data)
        flash("Dish updated.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dish_detail", dish_id=dish_id))


@bp.post("/dishes/<dish_id>/price")
def update_price(dish_id: str):
    price = request.form.get("price", "").strip()
    try:
        _client().update_price(dish_id, price)
        flash("Price updated and history recorded.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dish_detail", dish_id=dish_id))


@bp.post("/dishes/<dish_id>/toggle")
def toggle_dish(dish_id: str):
    try:
        d = _client().get_dish(dish_id)
        _client().update_dish(dish_id, {"is_available": not d["is_available"]})
        flash("Availability updated.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dishes"))


@bp.post("/dishes/<dish_id>/delete")
def delete_dish(dish_id: str):
    try:
        _client().delete_dish(dish_id)
        flash("Dish deleted.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dishes"))


# ─── Ingredients ─────────────────────────────────────────────────────────────��─

@bp.post("/dishes/<dish_id>/ingredients")
def add_ingredient(dish_id: str):
    product_id = request.form.get("product_id", "").strip()
    product_name = request.form.get("product_name", "").strip()
    unit = request.form.get("unit", "").strip()
    qty_raw = request.form.get("quantity", "").strip()

    if not product_id or not product_name or not unit or not qty_raw:
        flash("Заполните все поля ингредиента.", "danger")
        return redirect(url_for("menu.dish_detail", dish_id=dish_id))

    try:
        quantity = float(qty_raw)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        flash("Количество должно быть положительным числом.", "danger")
        return redirect(url_for("menu.dish_detail", dish_id=dish_id))

    try:
        _client().add_ingredient(dish_id, {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit": unit,
        })
        flash(f"Ингредиент «{product_name}» добавлен.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dish_detail", dish_id=dish_id))


@bp.post("/dishes/<dish_id>/ingredients/<ingredient_id>/delete")
def delete_ingredient(dish_id: str, ingredient_id: str):
    try:
        _client().delete_ingredient(dish_id, ingredient_id)
        flash("Ингредиент удалён.", "success")
    except ServiceError as e:
        flash(e.message, "danger")
    return redirect(url_for("menu.dish_detail", dish_id=dish_id))
