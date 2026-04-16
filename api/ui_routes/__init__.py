import os
from flask import Blueprint

_here = os.path.dirname(os.path.abspath(__file__))
_api_dir = os.path.dirname(_here)

ui_bp = Blueprint(
    "ui",
    __name__,
    template_folder=os.path.join(_api_dir, "templates"),
    static_folder=os.path.join(_api_dir, "static"),
)

from api.ui_routes.routes import auth, home, settings, user, admin  # noqa: F401, E402
