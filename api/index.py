import os
from flask import Flask, redirect, url_for
from flask import request

from api.api_routes import api_bp
from api.ui_routes import ui_bp
from utils.logger import log_event


# ========================= App Setup =========================
app = Flask(__name__)

# secret key is used to sign the session cookie so users cant tamper with it
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# tell Flask about all the route blueprints so it knows about the routes
app.register_blueprint(api_bp)

# ui_bp handles all the pages the user sees in the browser
app.register_blueprint(ui_bp, url_prefix="/ui")


# ========================= Root Route =========================

# redirects straight to the home page
@app.route("/")
def welcome():
    return redirect(url_for("ui.home"))



# ========================= Logging =========================

# this function runs automatically before every single request comes in
@app.before_request
def log_request():
    # should have MINIMUM: log entry with the http method and the path that was requested
    log_event("INFO", "request", request.method + " " + request.path, path=request.path, method=request.method)


# this function runs automatically after every single response goes out
# it must return the response or Flask will break the request
@app.after_request
def log_response(resp):
    # grab the numeric http status code from the response object
    statusCode = resp.status_code

    # log the status code so we can see what every request returned
    log_event("INFO", "request", "response " + str(statusCode), path=request.path, method=request.method, statusCode=statusCode)
    return resp


# ========================= Error Handlers =========================

# this function runs when a 400 bad request error happens
@app.errorhandler(400)
def bad_request(err):
    # log the error description then return a json error body with status 400
    log_event("ERROR", "error", "bad request: " + str(err.description), path=request.path, method=request.method, statusCode=400)
    return {"error": err.description}, 400


# this function runs when a 401 unauthorized error happens
@app.errorhandler(401)
def unauthorized(err):
    log_event("ERROR", "error", "unauthorized: " + str(err.description), path=request.path, method=request.method, statusCode=401)
    return {"error": "unauthorized"}, 401


# this function runs when a 403 forbidden error happens
@app.errorhandler(403)
def forbidden_error(err):
    log_event("ERROR", "error", "forbidden: " + str(err.description), path=request.path, method=request.method, statusCode=403)
    return {"error": "forbidden"}, 403


# this function runs when a 404 not found error happens
@app.errorhandler(404)
def not_found(err):
    log_event("ERROR", "error", "not found: " + str(err.description), path=request.path, method=request.method, statusCode=404)
    return {"error": "Not found"}, 404


# this function runs when a 500 internal server error happens
@app.errorhandler(500)
def server_error(err):
    # log the full error object so we can see what broke
    log_event("ERROR", "error", "server error: " + str(err), path=request.path, method=request.method, statusCode=500)
    return {"error": "server error"}, 500
