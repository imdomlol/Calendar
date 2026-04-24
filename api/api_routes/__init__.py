from flask import Blueprint

api_bp = Blueprint("api", __name__)

from api.api_routes.routes import (  # noqa: F401, E402
    calendar,
    event,
    external,
    guest,
    user,
)
