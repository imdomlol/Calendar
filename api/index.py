import logging
import os
from typing import Any

from flask import Flask, abort, g, redirect, request, url_for
from flask_cors import CORS
from supabase import create_client

from api.auth_routes import auth_bp
from api.ui_routes import ui_bp
from models.calendar import Calendar
from models.event import Event
from models.external import External
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-ui-secret-key")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(ui_bp, url_prefix="/ui")


@app.route("/")
def welcome():
    return redirect(url_for("ui.home"))


# Configure CORS to allow frontend
CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")


@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response


# Error handlers
@app.errorhandler(400)
def bad_request(e):
    logger.error(f"Bad request: {e.description}")
    return {"error": e.description}, 400


@app.errorhandler(401)
def unauthorized(e):
    logger.error(f"Unauthorized: {e.description}")
    return {"error": "Unauthorized"}, 401


@app.errorhandler(403)
def forbidden(e):
    logger.error(f"Forbidden: {e.description}")
    return {"error": "Forbidden"}, 403


@app.errorhandler(404)
def not_found(e):
    logger.error(f"Not found: {e.description}")
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return {"error": "Internal server error"}, 500


def _get_user_calendar_ids(supabase: Any, user_id: str) -> list[str]:
    owned = supabase.table("calendars").select("id").eq("owner_id", user_id).execute()
    member = (
        supabase.table("calendars")
        .select("id")
        .contains("member_ids", [user_id])
        .execute()
    )
    return list({c["id"] for c in owned.data} | {c["id"] for c in member.data})


@app.route("/calendars", methods=["GET"])
@require_auth
def list_calendars():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    owned = supabase.table("calendars").select("*").eq("owner_id", user_id).execute()
    member = (
        supabase.table("calendars")
        .select("*")
        .contains("member_ids", [user_id])
        .execute()
    )
    calendars = list({c["id"]: c for c in owned.data + member.data}.values())
    return {"calendars": calendars}


@app.route("/calendars", methods=["POST"])
@require_auth
def create_calendar():
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        abort(400, description="name is required")
    cal = Calendar(name=name, owner_id=user_id)
    result = cal.save()
    return result.data[0], 201


@app.route("/calendars/<calendar_id>", methods=["DELETE"])
@require_auth
def delete_calendar(calendar_id):
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


@app.route("/events", methods=["GET"])
@require_auth
def list_events():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    calendar_ids = _get_user_calendar_ids(supabase, user_id)
    if not calendar_ids:
        return {"events": []}
    result = (
        supabase.table("events")
        .select("*")
        .overlaps("calendar_ids", calendar_ids)
        .execute()
    )
    return {"events": result.data}


@app.route("/events", methods=["POST"])
@require_auth
def create_event():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendar_ids = body.get("calendar_ids", [])
    if not title or not calendar_ids:
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


@app.route("/events/<event_id>", methods=["PUT"])
@require_auth
def edit_event(event_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    user_cal_ids = set(_get_user_calendar_ids(supabase, user_id))
    existing = supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
    if not existing.data:
        abort(404)
    if not any(cid in user_cal_ids for cid in existing.data[0].get("calendar_ids", [])):
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
    if not updates:
        abort(
            400,
            description="no valid fields provided; allowed: title, description, start_timestamp, end_timestamp, calendar_ids",
        )
    result = supabase.table("events").update(updates).eq("id", event_id).execute()
    return result.data[0]


@app.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def delete_event(event_id):
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


@app.route("/externals", methods=["GET"])
@require_auth
def list_externals():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    result = supabase.table("externals").select("*").eq("user_id", user_id).execute()
    return {"externals": result.data}


@app.route("/externals", methods=["POST"])
@require_auth
def create_external():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    url = body.get("url")
    provider = body.get("provider")
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


@app.route("/externals/<external_id>", methods=["DELETE"])
@require_auth
def delete_external(external_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    existing = (
        supabase.table("externals")
        .select("id")
        .eq("id", external_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not existing.data:
        abort(404)
    supabase.table("externals").delete().eq("id", external_id).execute()
    return "", 204


@app.route("/me", methods=["GET"])
@require_auth
def me():
    user = getattr(g, "user", {})
    return {
        "id": user.get("id") or user.get("sub"),
        "email": user.get("email"),
        "role": user.get("role"),
        "last_sign_in_at": user.get("last_sign_in_at"),
    }, 200
