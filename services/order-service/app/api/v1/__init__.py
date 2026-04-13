from flask import Blueprint

from app.api.v1.orders import orders_bp

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1.register_blueprint(orders_bp)
