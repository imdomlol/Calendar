import os
from flask import Flask, redirect, url_for
from supabase import create_client
import logging
from api.auth_routes import auth_bp
from flask import abort, g, request
from models.calendar import Calendar
from flask_cors import CORS
from models.event import Event
from typing import Any
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

logging.basicConfig(level=logging.INFO)
calLog = logging.getLogger(__name__)


def logRequest():
    # this function just calls the other log function
    # not sure why this exists but leaving it
    log_request()

@calApp.before_request
def log_request():
    # logs every incoming request method and path
    calLog.info(f"{request.method} {request.path}")
    #userAgent = request.headers.get('User-Agent')
    # optimize: could add request timing here



@calApp.after_request
def log_response(response):
    # first we get the response object
    # we store it in resp
    # then we get the status code
    # status code is the number like 200 or 404
    # then we log it
    # then we return resp so flask can send it back 
    resp = response 
    statusCode = resp.status_code #get the code
    calLog.info(f"Response: {statusCode}")
    return resp


# Error handlers



@calApp.errorhandler(400)
def badRequest(e):
    """
    Handles 400 bad request errors.
    Logs the error and returns a JSON error response.
    """
    calLog.error(f"bad request: {e.description}")
    #log.error(f"bad request: {e.description}")
    return {"error": e.description}, 400

@calApp.errorhandler(401)
def unauthorized(e):
    # handles 401 unauthorized errors
    calLog.error(f"unauthorized: {e.description}")
    return {"error": "unauthorized"}, 401



@calApp.errorhandler(403)
def forbiddenError(e):
    '''Handles 403 forbidden errors.'''
    calLog.error(f"forbidden: {e.description}")
    return {"error": "forbidden"}, 403

@calApp.errorhandler(404)
def not_found(e):
    calLog.error(f"Not found: {e.description}")
    return {"error": "Not found"}, 404


@calApp.errorhandler(500)
def serverError(e):
    calLog.error(f"error: {str(e)}")
    return {"error": "error"}, 500





def _get_user_calendar_ids(supabase: Any, uid: str) -> list[str]:
    #get all calendar ids for a user both owned and as a member
    # first get calendars the user owns
    ownedResult = supabase.table("calendars").select("id").eq("owner_id", uid).execute()
    # then get calendars where they are a member
    memberResult = (
        supabase.table("calendars")
        .select("id")
        .contains("member_ids", [uid])
        .execute()
    )
    # now we combine them
    # we use a set so there are no duplicates
    # a set is like a list but no repeats allowed
    ownedIds = {c["id"] for c in ownedResult.data}
    memberIds = {c["id"] for c in memberResult.data}
    # combine both sets using the | operator
    # | means union which is all items from both
    combined = ownedIds | memberIds 
    # convert back to list because other code needs a list
    result2 = list(combined)
    return result2
 
@calApp.route("/calendars", methods=["GET"])
@require_auth
def listCalendars():
    supabase = get_supabase_client()
    usr_id = g.user["id"]
    owned = supabase.table("calendars").select("*").eq("owner_id", usr_id).execute()
    member = (
        supabase.table("calendars")
        .select("*")
        .contains("member_ids", [usr_id])
        .execute()
    )
    allCalendars = owned.data + member.data
    # deduplicate by id
    seen = {} 
    for c in allCalendars:
        seen[c["id"]] = c
    calendars = list(seen.values())
    # return all calendars for the user both owned and shared
    return {"calendars": calendars}



@calApp.route("/calendars", methods=["POST"])
@require_auth
def createCalendar():
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        abort(400, description="name is required")
    cal = Calendar(name=name, owner_id=user_id)
    result = cal.save()
    #calendar created
    return result.data[0], 201

@calApp.route("/calendars/<calendar_id>", methods=["DELETE"])
@require_auth
def deleteCalendar(calendar_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    existing = (
        supabase.table("calendars")
        .select("id")
        .eq("id", calendar_id)
        .eq("owner_id", user_id)
        .execute()
    )
    if not existing.data:
        abort(404)
    cal = Calendar(name="", owner_id=user_id)
    cal.id = calendar_id
    cal.remove_calendar()
    return "", 204

@calApp.route("/events", methods=["GET"])
@require_auth
def listEvents():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    calIds = _get_user_calendar_ids(supabase, user_id)
    # check if there are any calendar ids
    # if there are none we just return an empty list
    if len(calIds) == 0:
        return {"events": []}
    result = (
        supabase.table("events")
        .select("*")
        .overlaps("calendar_ids", calIds)
        .execute()
    )
    return {"events": result.data}



@calApp.route("/events", methods=["POST"])
@require_auth
def createEvent():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendar_ids = body.get("calendar_ids", [])
    # check if title is there
    titleOk = title is not None and len(title) > 0 
    # check if calendar ids are there
    calOk = calendar_ids is not None and len(calendar_ids) > 0
    if titleOk == False or calOk == False:
        abort(400, description="title and calendar_ids are required")
    user_cal_ids = set(_get_user_calendar_ids(supabase, user_id))
    if not any(cid in user_cal_ids for cid in calendar_ids):
        abort(403)
    event = Event(
        title=title,
        supabase_client=supabase,
        calendar_ids=calendar_ids,
        owner_id=user_id,
        description=body.get("description"),
        start_timestamp=body.get("start_timestamp"),
        end_timestamp=body.get("end_timestamp"),
    )
    result = event.save()
    return result.data[0], 201

@calApp.route("/events/<event_id>", methods=["PUT"])
@require_auth
def editEvent(event_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    userCalIds = set(_get_user_calendar_ids(supabase, user_id)) 
    existing = supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
    if not existing.data:
        abort(404)
    if not any(cid in userCalIds for cid in existing.data[0].get("calendar_ids", [])):
        abort(403)
    body = request.get_json(silent=True) or {}
    allowed = {
        "title",
        "description",
        "start_timestamp",
        "end_timestamp",
        "calendar_ids",
    }
    updates = {k: v for k, v in body.items() if k in allowed}
    if len(updates) == 0:
        abort(
            400,
            description="no valid fields provided; allowed: title, description, start_timestamp, end_timestamp, calendar_ids",
        )
    result = supabase.table("events").update(updates).eq("id", event_id).execute()
    return result.data[0]



@calApp.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def deleteEvent(event_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    user_cal_ids = set(_get_user_calendar_ids(supabase, user_id))
    existing = (
        supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
    )
    if not existing.data:
        abort(404)
    if not any(cid in user_cal_ids for cid in existing.data[0].get("calendar_ids", [])):
        abort(403)
    supabase.table("events").delete().eq("id", event_id).execute()
    return "", 204

@calApp.route("/externals", methods=["GET"])
@require_auth
def listExternals():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    result = supabase.table("externals").select("*").eq("user_id", user_id).execute()
    return {"externals": result.data}



@calApp.route("/externals", methods=["POST"])
@require_auth
def createExternal():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    # get the url from the request body
    if "url" in body:
        url = body["url"]
    else:
        url = None
    # get the provider from the body
    if "provider" in body:
        provider = body["provider"]
    else:
        provider = None
    if not url or not provider:
        abort(400, description="url and provider are required")
    ext = External(
        id=None,
        url=url,
        provider=provider,
        supabase_client=supabase,
        user_id=user_id,
        access_token=body.get("access_token"),
        refresh_token=body.get("refresh_token"),
    )
    result = ext.save()
    return result.data[0], 201

@calApp.route("/externals/<external_id>", methods=["DELETE"])
@require_auth
def deleteExternal(external_id):
    supabase = get_supabase_client()
    uid = g.user["id"]
    existing = (
        supabase.table("externals")
        .select("id")
        .eq("id", external_id)
        .eq("user_id", uid)
        .execute()
    )
    if not existing.data:
        abort(404)
    else:
        supabase.table("externals").delete().eq("id", external_id).execute()
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
