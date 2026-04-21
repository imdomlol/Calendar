import os
from flask import Blueprint

# figure out where the api directory is so we can find the templates and static folders
# __file__ is this file and dirname goes up one level to get the folder it lives in
_here = os.path.dirname(os.path.abspath(__file__))
_api_dir = os.path.dirname(_here)

# create the flask blueprint for all the ui routes
# the template and static folders are set relative to the api dir not this file
ui_bp = Blueprint(
    "ui",
    __name__,
    template_folder=os.path.join(_api_dir, "templates"),
    static_folder=os.path.join(_api_dir, "static"),
)

from api.ui_routes.routes import (  # noqa: F401, E402
    admin,
    auth,
    home,
    public,
    settings,
    user,
)
