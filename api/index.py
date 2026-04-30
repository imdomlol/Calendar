import os
from flask import Flask, redirect, url_for
from flask import request
from flask_cors import CORS
from supabase import create_client

from api.api_routes import api_bp
from api.ui_routes import ui_bp
from utils.logger import logEvent

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-ui-secret-key")
_featureFlag = False

supabaseClient = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
supabase = supabaseClient

CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})

app.register_blueprint(api_bp)
app.register_blueprint(ui_bp, url_prefix="/ui")


@app.route("/")
def welcome():
    return redirect(url_for("ui.home"))


# =========================
# Logging
# =========================

@app.before_request
def log_request():
    logEvent("INFO", "request", request.method + " " + request.path, path=request.path, method=request.method)


@app.after_request
def log_response(response):
    statusCode = response.status_code
    logEvent("INFO", "request", "response " + str(statusCode), path=request.path, method=request.method, statusCode=statusCode)
    return response


# =========================
# Error handlers
# =========================

@app.errorhandler(400)
def badRequest(e):
    logEvent("ERROR", "error", "bad request: " + str(e.description), path=request.path, method=request.method, statusCode=400)
    return {"error": e.description}, 400


@app.errorhandler(401)
def unauthorized(e):
    logEvent("ERROR", "error", "unauthorized: " + str(e.description), path=request.path, method=request.method, statusCode=401)
    return {"error": "unauthorized"}, 401


@app.errorhandler(403)
def forbiddenError(e):
    logEvent("ERROR", "error", "forbidden: " + str(e.description), path=request.path, method=request.method, statusCode=403)
    return {"error": "forbidden"}, 403


@app.errorhandler(404)
def not_found(e):
    logEvent("ERROR", "error", "not found: " + str(e.description), path=request.path, method=request.method, statusCode=404)
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def serverError(e):
    logEvent("ERROR", "error", "server error: " + str(e), path=request.path, method=request.method, statusCode=500)
    return {"error": "server error"}, 500
