import os
import secrets
from flask import Flask, redirect, url_for
from supabase import create_client
from api.auth_routes import auth_bp
from flask import abort, g, request
from utils.logger import logEvent
from models.calendar import Calendar
from flask_cors import CORS
from models.user import User
from api.ui_routes import ui_bp
from models.external import External
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client
# import sys


calApp = Flask(__name__)
appSecretKey = os.environ.get("FLASK_SECRET_KEY", "dev-ui-secret-key")
calApp.secret_key = appSecretKey

supabaseClient = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
supabase = supabaseClient

calApp.register_blueprint(auth_bp, url_prefix="/api/auth")
calApp.register_blueprint(ui_bp, url_prefix="/ui")
_featureFlag = False
# vercel needs a variable called app
# this just points to calApp so vercel can pick it up
app = calApp


@calApp.route("/")
def welcome():
    # this is the main entry point for the whole app
    # anyone who visits / gets sent to the ui home page
    # we use url_for to get the url so we dont hardcode the path
    # ui.home is the name of the home route in the ui blueprint
    homeTarget = url_for("ui.home") #get the url for home
    # now send the browser there
    return redirect(homeTarget)

# Configure CORS
CORS(calApp, resources={r"/api/*": {"origins": "https://your-domain.com"}})

@calApp.before_request
def log_request():
    logEvent("INFO", "request", request.method + " " + request.path, path=request.path, method=request.method)


@calApp.after_request
def log_response(response):
    statusCode = response.status_code
    logEvent("INFO", "request", "response " + str(statusCode), path=request.path, method=request.method, statusCode=statusCode)
    return response


# Error handlers



@calApp.errorhandler(400)
def badRequest(e):
    logEvent("ERROR", "error", "bad request: " + str(e.description), path=request.path, method=request.method, statusCode=400)
    return {"error": e.description}, 400

@calApp.errorhandler(401)
def unauthorized(e):
    logEvent("ERROR", "error", "unauthorized: " + str(e.description), path=request.path, method=request.method, statusCode=401)
    return {"error": "unauthorized"}, 401

@calApp.errorhandler(403)
def forbiddenError(e):
    logEvent("ERROR", "error", "forbidden: " + str(e.description), path=request.path, method=request.method, statusCode=403)
    return {"error": "forbidden"}, 403

@calApp.errorhandler(404)
def not_found(e):
    logEvent("ERROR", "error", "not found: " + str(e.description), path=request.path, method=request.method, statusCode=404)
    return {"error": "Not found"}, 404

@calApp.errorhandler(500)
def serverError(e):
    logEvent("ERROR", "error", "server error: " + str(e), path=request.path, method=request.method, statusCode=500)
    return {"error": "error"}, 500





def _make_user() -> User:
    # build a User from the authenticated request context
    return User(
        user_id=g.user["id"],
        display_name=g.user.get("display_name", ""),
        email=g.user.get("email", "")
    )


@calApp.route("/calendars", methods=["GET"])
@require_auth
def listCalendars():
    user = _make_user()
    return {"calendars": user.listCalendars()}



@calApp.route("/calendars", methods=["POST"])
@require_auth
def createCalendar():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        abort(400, description="name is required")
    user = _make_user()
    result = user.createCalendar(name)
    return result.data[0], 201

@calApp.route("/calendars/<calendar_id>", methods=["DELETE"])
@require_auth
def deleteCalendar(calendar_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    existing = supabase.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", user_id).execute()
    if not existing.data:
        abort(404)
    user = _make_user()
    user.removeCalendar(calendar_id)
    return "", 204

@calApp.route("/events", methods=["GET"])
@require_auth
def listEvents():
    user = _make_user()
    return {"events": user.listEvents()}



@calApp.route("/events", methods=["POST"])
@require_auth
def createEvent():
    user = _make_user()
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendar_ids = body.get("calendar_ids", [])
    titleOk = title is not None and len(title) > 0
    calOk = calendar_ids is not None and len(calendar_ids) > 0
    if titleOk == False or calOk == False:
        abort(400, description="title and calendar_ids are required")
    # make sure the user actually has access to the calendars they specified
    user_cal_ids = set(c["id"] for c in user.listCalendars())
    if not any(cid in user_cal_ids for cid in calendar_ids):
        abort(403)
    result = user.createEvent(
        title=title,
        calendar_ids=calendar_ids,
        description=body.get("description"),
        start_timestamp=body.get("start_timestamp"),
        end_timestamp=body.get("end_timestamp"),
    )
    return result.data[0], 201

@calApp.route("/events/<event_id>", methods=["PUT"])
@require_auth
def editEvent(event_id):
    user = _make_user()
    # check the event exists and belongs to one of the user's calendars
    supabase = get_supabase_client()
    existing = supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
    if not existing.data:
        abort(404)
    userCalIds = set(c["id"] for c in user.listCalendars())
    if not any(cid in userCalIds for cid in existing.data[0].get("calendar_ids", [])):
        abort(403)
    body = request.get_json(silent=True) or {}
    allowed = {"title", "description", "start_timestamp", "end_timestamp", "calendar_ids"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if len(updates) == 0:
        abort(400, description="no valid fields provided; allowed: title, description, start_timestamp, end_timestamp, calendar_ids")
    result = user.editEvent(event_id, **updates)
    return result.data[0]



@calApp.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def deleteEvent(event_id):
    user = _make_user()
    supabase = get_supabase_client()
    existing = supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
    if not existing.data:
        abort(404)
    userCalIds = set(c["id"] for c in user.listCalendars())
    if not any(cid in userCalIds for cid in existing.data[0].get("calendar_ids", [])):
        abort(403)
    user.removeEvent(event_id)
    return "", 204

@calApp.route("/externals", methods=["GET"])
@require_auth
def listExternals():
    user = _make_user()
    return {"externals": user.listExternals()}



@calApp.route("/externals", methods=["POST"])
@require_auth
def createExternal():
    body = request.get_json(silent=True) or {}
    url = body.get("url")
    provider = body.get("provider")
    if not url or not provider:
        abort(400, description="url and provider are required")
    user = _make_user()
    result = user.addExternal(
        url=url,
        provider=provider,
        access_token=body.get("access_token"),
        refresh_token=body.get("refresh_token"),
    )
    return result.data[0], 201

@calApp.route("/externals/<external_id>", methods=["DELETE"])
@require_auth
def deleteExternal(external_id):
    user = _make_user()
    try:
        user.removeExternal(external_id)
    except ValueError:
        abort(404)
    return "", 204


@calApp.route("/me", methods=["GET"])
@require_auth
def getMe():
    user = getattr(g, "user", {})
    uid = user.get("id") or user.get("sub") #get the user id
    userEmail = user.get("email")
    userRole = user.get("role")
    lastSignIn = user.get("last_sign_in_at")
    return {
        "id": uid,
        "email": userEmail,
        "role": userRole,
        "last_sign_in_at": lastSignIn,
    }, 200


@calApp.route("/me", methods=["DELETE"])
@require_auth
def deleteMe():
    user = _make_user()
    user.removeSelf()
    return "", 204


@calApp.route("/calendars/<calendar_id>/guest-link", methods=["POST"])
@require_auth
def createGuestLink(calendar_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    # only the owner can create a guest link
    existing = supabase.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", user_id).execute()
    if not existing.data:
        abort(404)
    body = request.get_json(silent=True) or {}
    role = body.get("role", "viewer")
    if role not in ("viewer", "editor"):
        abort(400, description="role must be viewer or editor")
    token = secrets.token_urlsafe(32)
    result = supabase.table("calendars").update({
        "guest_link_token": token,
        "guest_link_role": role,
        "guest_link_active": True,
    }).eq("id", calendar_id).execute()
    return result.data[0], 200


@calApp.route("/calendars/<calendar_id>/guest-link", methods=["DELETE"])
@require_auth
def revokeGuestLink(calendar_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    # only the owner can revoke a guest link
    existing = supabase.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", user_id).execute()
    if not existing.data:
        abort(404)
    supabase.table("calendars").update({
        "guest_link_token": None,
        "guest_link_role": None,
        "guest_link_active": False,
    }).eq("id", calendar_id).execute()
    return "", 204


@calApp.route("/calendars/<calendar_id>/members", methods=["POST"])
@require_auth
def addMember(calendar_id):
    body = request.get_json(silent=True) or {}
    member_id = body.get("member_id")
    if not member_id:
        abort(400, description="member_id is required")
    user = _make_user()
    try:
        user.addMember(calendar_id, member_id)
    except Exception as e:
        abort(400, description=str(e))
    return {"member_id": member_id}, 201


@calApp.route("/calendars/<calendar_id>/members/<member_id>", methods=["DELETE"])
@require_auth
def removeMember(calendar_id, member_id):
    user = _make_user()
    try:
        user.removeMember(calendar_id, member_id)
    except ValueError:
        abort(404)
    return "", 204


@calApp.route("/friends", methods=["GET"])
@require_auth
def listFriends():
    user = _make_user()
    friends = user.listFriends()
    return {"friends": friends}


@calApp.route("/friends", methods=["POST"])
@require_auth
def addFriend():
    body = request.get_json(silent=True) or {}
    friend_id = body.get("friend_id")
    email = body.get("email")
    user = _make_user()
    try:
        friends = user.addFriend(friend_id=friend_id, email=email)
    except ValueError as e:
        abort(400, description=str(e))
    return {"friends": friends}


@calApp.route("/friends/<friend_id>", methods=["DELETE"])
@require_auth
def removeFriend(friend_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    result = supabase.table("users").select("friends").eq("id", user_id).execute()
    if not result.data:
        abort(404)
    friends = result.data[0].get("friends") or []
    if friend_id not in friends:
        abort(404)
    friends.remove(friend_id)
    supabase.table("users").update({"friends": friends}).eq("id", user_id).execute()
    return "", 204
