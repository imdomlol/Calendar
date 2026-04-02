from http.server import BaseHTTPRequestHandler
import json
import os
from supabase import create_client
from auth_routes import auth_bp
from flask import Flask, request, g, abort
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client
from models.calendar import Calendar
from models.event import Event
from models.external import External
from flask_cors import CORS
from utils.auth import require_auth

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

app.register_blueprint(auth_bp, url_prefix="/api/auth")

app = Flask(__name__)

@app.route("/")
def welcome():
    return {"message": "Welcome to the API!"}

# Configure CORS to allow frontend
CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})

# Logging
import logging
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
    logger.error(f"Bad request: {str(e)}")
    return {"error": str(e)}, 400

@app.errorhandler(401)
def unauthorized(e):
    logger.error(f"Unauthorized: {str(e)}")
    return {"error": "Unauthorized"}, 401

@app.errorhandler(404)
def not_found(e):
    logger.error(f"Not found: {str(e)}")
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return {"error": "Internal server error"}, 500

def _get_user_calendar_ids(supabase, user_id):
    owned = supabase.table("calendars").select("id").eq("owner_id", user_id).execute()
    member = supabase.table("calendars").select("id").contains("member_ids", [user_id]).execute()
    return list({c["id"] for c in owned.data} | {c["id"] for c in member.data})


@app.route("/calendars", methods=["GET"])
@require_auth
def list_calendars():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    owned = supabase.table("calendars").select("*").eq("owner_id", user_id).execute()
    member = supabase.table("calendars").select("*").contains("member_ids", [user_id]).execute()
    calendars = list({c["id"]: c for c in owned.data + member.data}.values())
    return {"calendars": calendars}


@app.route("/calendars", methods=["POST"])
@require_auth
def create_calendar():
    supabase = get_supabase_client()
    user_id = g.user["id"]
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        abort(400)
    cal = Calendar(name=name, owner_id=user_id)
    result = cal.save()
    return result.data[0], 201


@app.route("/calendars/<calendar_id>", methods=["DELETE"])
@require_auth
def delete_calendar(calendar_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    existing = supabase.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", user_id).execute()
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
    result = supabase.table("events").select("*").overlaps("calendar_ids", calendar_ids).execute()
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
        abort(400)
    user_cal_ids = set(_get_user_calendar_ids(supabase, user_id))
    if not any(cid in user_cal_ids for cid in calendar_ids):
        abort(403)
    event = Event(
        title=title,
        supabase_client=supabase,
        calendar_ids=calendar_ids,
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
    existing = supabase.table("events").select("*").eq("id", event_id).execute()
    if not existing.data:
        abort(404)
    if not any(cid in user_cal_ids for cid in existing.data[0].get("calendar_ids", [])):
        abort(403)
    body = request.get_json(silent=True) or {}
    allowed = {"title", "description", "start_timestamp", "end_timestamp", "calendar_ids"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        abort(400)
    result = supabase.table("events").update(updates).eq("id", event_id).execute()
    return result.data[0]


@app.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def delete_event(event_id):
    supabase = get_supabase_client()
    user_id = g.user["id"]
    user_cal_ids = set(_get_user_calendar_ids(supabase, user_id))
    existing = supabase.table("events").select("calendar_ids").eq("id", event_id).execute()
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
        abort(400)
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
    existing = supabase.table("externals").select("id").eq("id", external_id).eq("user_id", user_id).execute()
    if not existing.data:
        abort(404)
    supabase.table("externals").delete().eq("id", external_id).execute()
    return "", 204



@app.route("/me", methods=["GET"])
@require_auth
def me():
    user = getattr(g, "user", {})
    return {
        "success": True,
        "user": {
            "id": user.get("id") or user.get("sub"),
            "email": user.get("email"),
            "role": user.get("role"),
            "last_sign_in_at": user.get("last_sign_in_at"),
        },
        "session": {
            "authenticated": True,
        },
    }, 200

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"message": "Welcome to the API!"}')

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            name = data.get("name")
            email = data.get("email")

            if not name or not email:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Name and email are required"}')
                return

            response = supabase.table("users").insert({"name": name, "email": email}).execute()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message": "User created successfully"}')

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())