import secrets
from flask import Blueprint, abort, g, request
from models.calendar import Calendar
from utils.auth import require_auth
from utils.request_helpers import makeUser
from utils.supabase_client import get_supabase_client

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/calendars", methods=["GET"])
@require_auth
def listCalendars():
    user = makeUser()
    return {"calendars": user.listCalendars()}


@calendar_bp.route("/calendars", methods=["POST"])
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


@calendar_bp.route("/calendars/<calendar_id>", methods=["DELETE"])
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


@calendar_bp.route("/calendars/<calendar_id>/members", methods=["POST"])
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


@calendar_bp.route("/calendars/<calendar_id>/members/<member_id>", methods=["DELETE"])
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


@calendar_bp.route("/calendars/<calendar_id>/guest-link", methods=["POST"])
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


@calendar_bp.route("/calendars/<calendar_id>/guest-link", methods=["DELETE"])
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
