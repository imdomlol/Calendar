from flask import Blueprint, abort, request
from utils.supabase_client import get_supabase_client

guest_bp = Blueprint("guest", __name__)


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


@guest_bp.route("/guest/<token>/events", methods=["POST"])
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


@guest_bp.route("/guest/<token>/events/<event_id>", methods=["PUT"])
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


@guest_bp.route("/guest/<token>/events/<event_id>", methods=["DELETE"])
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
