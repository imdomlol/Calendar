from flask import abort, request
from api.api_routes import api_bp
from api.api_routes.helpers import makeUser
from models.event import Event
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client


@api_bp.route("/events", methods=["GET"])
@require_auth
def listEvents():
    user = makeUser()
    return {"events": user.listEvents()}


@api_bp.route("/events", methods=["POST"])
@require_auth
def createEvent():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendarIds = body.get("calendar_ids", [])

    titleOk = title is not None and len(title) > 0
    calOk = calendarIds is not None and len(calendarIds) > 0
    if not titleOk or not calOk:
        abort(400, description="title and calendar_ids are required")

    user = makeUser()
    userCalIds = [cal["id"] for cal in user.listCalendars()]

    if not any(cid in userCalIds for cid in calendarIds):
        abort(403)

    event = Event(
        title=title,
        calendarIds=calendarIds,
        ownerId=user.userId,
        description=body.get("description"),
        startTimestamp=body.get("start_timestamp"),
        endTimestamp=body.get("end_timestamp"),
    )
    result = event.save()
    return result.data[0], 201


@api_bp.route("/events/bulk", methods=["POST"])
@require_auth
def createEventsBulk():
    body = request.get_json(silent=True) or {}
    events_list = body.get("events", [])
    if not events_list:
        abort(400, description="events list is required")

    user = makeUser()
    userCalIds = [cal["id"] for cal in user.listCalendars()]

    db = get_supabase_client()
    payloads = []
    for evt in events_list:
        title = (evt.get("title") or "").strip()
        calendarIds = evt.get("calendar_ids") or []
        if not title or not calendarIds:
            continue
        if not any(cid in userCalIds for cid in calendarIds):
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


@api_bp.route("/events/<event_id>", methods=["PUT"])
@require_auth
def editEvent(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        abort(404)

    eventData = result.data[0]

    user = makeUser()
    userCalIds = [cal["id"] for cal in user.listCalendars()]

    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        abort(403)

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    description = body.get("description")
    startTimestamp = body.get("start_timestamp")
    endTimestamp = body.get("end_timestamp")
    calendarIds = body.get("calendar_ids")

    if title is None and description is None and startTimestamp is None and endTimestamp is None and calendarIds is None:
        abort(400, description="no valid fields provided; allowed: title, description, start_timestamp, end_timestamp, calendar_ids")

    event = Event(
        title=eventData["title"],
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


@api_bp.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def removeEvent(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        abort(404)
    eventData = result.data[0]
    user = makeUser()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        abort(403)
    event = Event(
        title=eventData["title"],
        calendarIds=eventData["calendar_ids"],
    )
    event.id = event_id
    event.remove()
    return "", 204
