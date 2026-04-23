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
from models.event import Event
from api.ui_routes import ui_bp
from models.external import External
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client

# vercel needs a variable called app
app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(ui_bp, url_prefix="/ui")
_featureFlag = False

appSecretKey = os.environ.get("FLASK_SECRET_KEY", "dev-ui-secret-key")
app.secret_key = appSecretKey

supabaseClient = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
supabase = supabaseClient

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})

@app.route("/")
def welcome():
    # send anyone who visits / to the ui home page
    homeTarget = url_for("ui.home")
    return redirect(homeTarget)

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


def makeUser() -> User:
    # build a User object from the current request context
    return User(
        userId=g.user["id"],
        displayName=g.user.get("display_name", ""),
        email=g.user.get("email", "")
    )

# =========================
# Calendar routes
# =========================

@app.route("/calendars", methods=["POST"])
@require_auth
def createCalendar():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        abort(400, description="name is required")
    userId = g.user["id"]
    cal = Calendar(name=name, ownerId=userId)
    result = cal.save()
    return result.data[0], 201

@app.route("/calendars/<calendar_id>", methods=["DELETE"])
@require_auth
def deleteCalendar(calendar_id):
    db = get_supabase_client()
    userId = g.user["id"]
    existing = db.table("calendars").select("id", "name", "owner_id").eq("id", calendar_id).eq("owner_id", userId).execute()
    if not existing.data:
        abort(404)
    calData = existing.data[0]
    cal = Calendar(name=calData["name"], ownerId=calData["owner_id"])
    cal.id = calendar_id
    cal.remove()
    return "", 204

@app.route("/calendars/<calendar_id>/members", methods=["POST"])
@require_auth
def addMember(calendar_id):
    body = request.get_json(silent=True) or {}
    memberIds = body.get("member_id")
    if not memberIds:
        abort(400, description="member_id is required")
    if isinstance(memberIds, str):
        memberIds = [memberIds]
    elif not isinstance(memberIds, list):
        abort(400, description="member_id must be a string or list of strings")
    db = get_supabase_client()
    result = db.table("calendars").select("*").eq("id", calendar_id).execute()
    if not result.data:
        abort(404, description="Calendar not found")
    calData = result.data[0]
    cal = Calendar(name=calData["name"], ownerId=calData["owner_id"])
    cal.id = calendar_id
    cal.memberIds = calData["member_ids"]
    added = []
    errors = {}
    for mid in memberIds:
        try:
            cal.add_member(mid)
            added.append(mid)
        except Exception as e:
            errors[mid] = str(e)
    if errors and not added:
        abort(400, description=f"No members added: {errors}")
    return {"added": added, "errors": errors}, 201

@app.route("/calendars/<calendar_id>/members/<member_id>", methods=["DELETE"])
@require_auth
def removeMember(calendar_id, member_id):
    db = get_supabase_client()
    result = db.table("calendars").select("*").eq("id", calendar_id).execute()
    if not result.data:
        abort(404, description="Calendar not found")
    calData = result.data[0]
    cal = Calendar(name=calData["name"], ownerId=calData["owner_id"])
    cal.id = calendar_id
    cal.memberIds = calData["member_ids"]
    try:
        cal.remove_member(member_id)
    except KeyError:
        abort(404, description="Member not found")
    return "", 204

# =========================
# Guest routes
# =========================

@app.route("/calendars/<calendar_id>/guest-link", methods=["POST"])
@require_auth
def createGuestLink(calendar_id):
    db = get_supabase_client()
    userId = g.user["id"]
    existing = db.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", userId).execute()
    if not existing.data:
        abort(404)
    body = request.get_json(silent=True) or {}
    role = body.get("role", "viewer")
    if role not in ("viewer", "editor"):
        abort(400, description="role must be viewer or editor")
    token = secrets.token_urlsafe(32)
    result = db.table("calendars").update({
        "guest_link_token": token,
        "guest_link_role": role,
        "guest_link_active": True,
    }).eq("id", calendar_id).execute()
    return result.data[0], 200

@app.route("/calendars/<calendar_id>/guest-link", methods=["DELETE"])
@require_auth
def revokeGuestLink(calendar_id):
    db = get_supabase_client()
    userId = g.user["id"]
    existing = db.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", userId).execute()
    if not existing.data:
        abort(404)
    db.table("calendars").update({
        "guest_link_token": None,
        "guest_link_role": None,
        "guest_link_active": False,
    }).eq("id", calendar_id).execute()
    return "", 204

# =========================
# Event routes
# =========================

@app.route("/events", methods=["POST"])
@require_auth
def createEvent():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendarIds = body.get("calendar_ids", [])

    titleOk = title is not None and len(title) > 0
    calOk = calendarIds is not None and len(calendarIds) > 0
    if not titleOk or not calOk:
        abort(400, description="title and calendar_ids are required")

    # make sure the user owns or is a member of at least one of the given calendars
    user = makeUser()
    userCals = user.listCalendars()
    userCalIds = []
    for cal in userCals:
        userCalIds.append(cal["id"])

    hasAccess = False
    for cid in calendarIds:
        if cid in userCalIds:
            hasAccess = True
    if not hasAccess:
        abort(403)

    db = get_supabase_client()
    event = Event(
        title=title,
        supabaseClient=db,
        calendarIds=calendarIds,
        ownerId=user.userId,
        description=body.get("description"),
        startTimestamp=body.get("start_timestamp"),
        endTimestamp=body.get("end_timestamp"),
    )
    result = event.save()
    return result.data[0], 201

@app.route("/events/<event_id>", methods=["PUT"])
@require_auth
def editEvent(event_id):
    db = get_supabase_client()

    # get the event and check it exists
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        abort(404)

    eventData = result.data[0]

    # check the user has access to at least one of this event's calendars
    user = makeUser()
    userCals = user.listCalendars()
    userCalIds = []
    for cal in userCals:
        userCalIds.append(cal["id"])

    hasAccess = False
    for cid in eventData.get("calendar_ids", []):
        if cid in userCalIds:
            hasAccess = True
    if not hasAccess:
        abort(403)

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    description = body.get("description")
    startTimestamp = body.get("start_timestamp")
    endTimestamp = body.get("end_timestamp")
    calendarIds = body.get("calendar_ids")

    # make sure at least one field was given
    if title is None and description is None and startTimestamp is None and endTimestamp is None and calendarIds is None:
        abort(400, description="no valid fields provided; allowed: title, description, start_timestamp, end_timestamp, calendar_ids")

    event = Event(
        title=eventData["title"],
        supabaseClient=db,
        calendarIds=eventData["calendar_ids"],
        ownerId=eventData["owner_id"],
    )
    event.id = event_id
    editResult = event.edit(
        title=title,
        description=description,
        startTimestamp=startTimestamp,
        endTimestamp=endTimestamp,
        calendarIds=calendarIds,
    )
    return editResult.data[0], 200

@app.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def removeEvent(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        abort(404)
    eventData = result.data[0]
    event = Event(
        title=eventData["title"],
        supabaseClient=db,
        calendarIds=eventData["calendar_ids"],
    )
    event.id = event_id
    event.remove()
    return "", 204

# =========================
# External calendar
# =========================

@app.route("/externals/<external_id>/pull", methods=["POST"])
@require_auth
def pullExternalData(external_id):
    db = get_supabase_client()
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
    )
    try:
        data = ext.pullCalData(external_id)
    except Exception as e:
        abort(500, description=f"Failed to pull data: {e}")
    return {"data": data}, 200

@app.route("/externals/<external_id>/push", methods=["POST"])
@require_auth
def pushExternalData(external_id):
    db = get_supabase_client()
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
    )
    try:
        data = ext.pushCalData(external_id)
    except Exception as e:
        abort(500, description=f"Failed to push data: {e}")
    return {"data": data}, 200

@app.route("/externals", methods=["POST"])
@require_auth
def createExternal():
    body = request.get_json(silent=True) or {}
    url = body.get("url")
    provider = body.get("provider")
    if not url or not provider:
        abort(400, description="url and provider are required")
    user = makeUser()
    db = get_supabase_client()
    ext = External(
        id=None,
        url=url,
        provider=provider,
        supabaseClient=db,
        userId=user.userId,
        accessToken=body.get("access_token"),
        refreshToken=body.get("refresh_token"),
    )
    result = ext.save()
    return result.data[0], 201

@app.route("/externals/<external_id>", methods=["DELETE"])
@require_auth
def deleteExternal(external_id):
    user = makeUser()
    db = get_supabase_client()
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
        userId=user.userId,
    )
    try:
        ext.remove(external_id)
    except ValueError:
        abort(404)
    return "", 204

# =========================
# User-related routes
# =========================

@app.route("/externals", methods=["GET"])
@require_auth
def listExternals():
    user = makeUser()
    return {"externals": user.listExternals()}

@app.route("/events", methods=["GET"])
@require_auth
def listEvents():
    user = makeUser()
    return {"events": user.listEvents()}

@app.route("/calendars", methods=["GET"])
@require_auth
def listCalendars():
    user = makeUser()
    return {"calendars": user.listCalendars()}

@app.route("/me", methods=["GET"])
@require_auth
def getMe():
    user = getattr(g, "user", {})
    uid = user.get("id") or user.get("sub")
    userEmail = user.get("email")
    userRole = user.get("role")
    lastSignIn = user.get("last_sign_in_at")
    return {
        "id": uid,
        "email": userEmail,
        "role": userRole,
        "last_sign_in_at": lastSignIn,
    }, 200

@app.route("/me", methods=["DELETE"])
@require_auth
def deleteMe():
    user = makeUser()
    user.removeAccount()
    return "", 204

@app.route("/friends", methods=["GET"])
@require_auth
def listFriends():
    user = makeUser()
    friends = user.listFriends()
    return {"friends": friends}

@app.route("/friends", methods=["POST"])
@require_auth
def addFriend():
    body = request.get_json(silent=True) or {}
    friendId = body.get("friend_id")
    email = body.get("email")
    user = makeUser()
    try:
        friends = user.addFriend(friendId=friendId, email=email)
    except ValueError as e:
        abort(400, description=str(e))
    return {"friends": friends}

@app.route("/friends/<friend_id>", methods=["DELETE"])
@require_auth
def removeFriend(friend_id):
    user = makeUser()
    try:
        user.removeFriend(friend_id)
    except ValueError as e:
        abort(404, description=str(e))
    return "", 204

# =========================
# Bulk event routes
# =========================

@app.route("/events/bulk", methods=["POST"])
@require_auth
def createEventsBulk():
    body = request.get_json(silent=True) or {}
    events_list = body.get("events", [])
    if not events_list:
        abort(400, description="events list is required")

    user = makeUser()
    userCals = user.listCalendars()
    userCalIds = []
    for cal in userCals:
        userCalIds.append(cal["id"])

    db = get_supabase_client()
    payloads = []
    for evt in events_list:
        title = (evt.get("title") or "").strip()
        calendarIds = evt.get("calendar_ids") or []
        if not title or not calendarIds:
            continue
        hasAccess = False
        for cid in calendarIds:
            if cid in userCalIds:
                hasAccess = True
        if not hasAccess:
            continue
        payloads.append({
            "title": title,
            "owner_id": user.userId,
            "calendar_ids": calendarIds,
            "description": evt.get("description") or None,
            "start_timestamp": evt.get("start_timestamp") or None,
            "end_timestamp": evt.get("end_timestamp") or None,
        })

    if not payloads:
        return {"created": 0}, 200

    result = db.table("events").insert(payloads).execute()
    return {"created": len(result.data or [])}, 201

# =========================
# Guest event routes
# =========================

def _get_guest_editor_calendar(token):
    db = get_supabase_client()
    result = (
        db.table("calendars")
        .select("id, name, owner_id, guest_link_role, guest_link_active")
        .eq("guest_link_token", token)
        .eq("guest_link_active", "true")
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    cal = result.data[0]
    if str(cal.get("guest_link_role") or "viewer").lower() != "editor":
        return None
    return cal

@app.route("/guest/<token>/events", methods=["POST"])
def guestCreateEvent(token):
    cal = _get_guest_editor_calendar(token)
    if not cal:
        abort(403)
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        abort(400, description="title is required")
    db = get_supabase_client()
    pload = {
        "title": title,
        "owner_id": cal["owner_id"],
        "calendar_ids": [str(cal["id"])],
        "description": body.get("description") or None,
        "start_timestamp": body.get("start_timestamp") or None,
        "end_timestamp": body.get("end_timestamp") or None,
    }
    result = db.table("events").insert(pload).execute()
    return result.data[0], 201

@app.route("/guest/<token>/events/<event_id>", methods=["PUT"])
def guestEditEvent(token, event_id):
    cal = _get_guest_editor_calendar(token)
    if not cal:
        abort(403)
    cal_id = str(cal["id"])
    db = get_supabase_client()
    existing = (
        db.table("events")
        .select("id")
        .eq("id", event_id)
        .overlaps("calendar_ids", [cal_id])
        .limit(1)
        .execute()
    )
    if not existing.data:
        abort(404)
    body = request.get_json(silent=True) or {}
    updates = {
        "description": body.get("description") or None,
        "start_timestamp": body.get("start_timestamp") or None,
        "end_timestamp": body.get("end_timestamp") or None,
    }
    title = (body.get("title") or "").strip()
    if title:
        updates["title"] = title
    result = db.table("events").update(updates).eq("id", event_id).execute()
    return result.data[0], 200

@app.route("/guest/<token>/events/<event_id>", methods=["DELETE"])
def guestDeleteEvent(token, event_id):
    cal = _get_guest_editor_calendar(token)
    if not cal:
        abort(403)
    cal_id = str(cal["id"])
    db = get_supabase_client()
    existing = (
        db.table("events")
        .select("id")
        .eq("id", event_id)
        .overlaps("calendar_ids", [cal_id])
        .limit(1)
        .execute()
    )
    if not existing.data:
        abort(404)
    db.table("events").delete().eq("id", event_id).execute()
    return "", 204
