from flask import Flask

from app.config import settings


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = settings.secret_key
    app.config["DEBUG"] = settings.debug

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.views.auth import bp as auth_bp
    from app.views.dashboard import bp as dash_bp
    from app.views.menu import bp as menu_bp
    from app.views.warehouse import bp as wh_bp
    from app.views.orders import bp as orders_bp
    from app.views.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(wh_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    # ── Auth middleware ───────────────────────────────────────────────────────
    from app.middleware.auth import init_auth, has_permission
    init_auth(app)
    app.jinja_env.globals["has_permission"] = has_permission

    # ── Template filters ─────────────────────────────────────────────────────
    @app.template_filter("fmt_price")
    def fmt_price(value):
        try:
            return f"{float(value):,.2f} ₽"
        except (TypeError, ValueError):
            return value

    @app.template_filter("fmt_stock")
    def fmt_stock(value):
        try:
            v = float(value)
            return f"{v:g}"
        except (TypeError, ValueError):
            return value

    @app.template_filter("fmt_dt")
    def fmt_dt(value):
        if not value:
            return "—"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return value

    return app
