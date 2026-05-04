from flask import Blueprint

api_bp = Blueprint("api", __name__)

# REST API: webhook receivers + guest token endpoints only
# UI uses session auth via ui_routes. do not add UI handlers here
from api.api_routes.routes import (  # noqa: F401, E402
    guest,
    webhooks,
)
