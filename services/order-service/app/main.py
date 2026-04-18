from flask import Flask, jsonify

from app.config import settings
from app.extensions import db, migrate


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)

    db_url = "sqlite:///:memory:" if testing else settings.database_url
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = testing
    app.config["DEBUG"] = settings.debug

    db.init_app(app)
    migrate.init_app(app, db)

    # Register models so SQLAlchemy knows about them
    from app.models import Order, OrderItem, OrderStatus  # noqa: F401

    # Register blueprints
    from app.api.v1 import api_v1
    app.register_blueprint(api_v1)

    @app.get("/health")
    def health():  # type: ignore[no-untyped-def]
        return jsonify({"status": "ok", "service": settings.app_name})

    @app.errorhandler(404)
    def not_found(exc):  # type: ignore[no-untyped-def]
        return jsonify({"detail": str(exc)}), 404

    @app.errorhandler(409)
    def conflict(exc):  # type: ignore[no-untyped-def]
        return jsonify({"detail": str(exc)}), 409

    @app.errorhandler(422)
    def unprocessable(exc):  # type: ignore[no-untyped-def]
        return jsonify({"detail": str(exc)}), 422

    @app.errorhandler(503)
    def service_unavailable(exc):  # type: ignore[no-untyped-def]
        return jsonify({"detail": str(exc)}), 503

    @app.errorhandler(500)
    def internal_error(exc):  # type: ignore[no-untyped-def]
        return jsonify({"detail": "Internal server error", "error": str(exc)}), 500

    return app
