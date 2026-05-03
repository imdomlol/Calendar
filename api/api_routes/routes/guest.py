from flask import abort, request
from api.api_routes import api_bp
from models.event import Event
from utils.supabase_client import get_supabase_client


# ========================= Guest Helpers =========================

# find the calendar for a guest editor token
def _get_guest_editor_calendar(token):
    db = get_supabase_client()

    # check for an active guest link with this token
    query = db.table("calendars")
    query = query.select("id, name, owner_id, guest_link_role, guest_link_active")
    query = query.eq("guest_link_token", token)
    query = query.eq("guest_link_active", "true")
    query = query.limit(1)
    result = query.execute()

    if not result.data:
        return None

    calendar = result.data[0]

    # only editor links can change events
    rawRole = calendar.get("guest_link_role")
    if rawRole:
        guestRole = str(rawRole).lower()
    else:
        guestRole = "viewer"

    if guestRole != "editor":
        return None
    return calendar


# ========================= Event Routes =========================

# create an event from a guest calendar link
@api_bp.route("/guest/<token>/events", methods=["POST"])
def guest_create_event(token):
    calendar = _get_guest_editor_calendar(token)
    if not calendar:
        abort(403)

    # read the JSON body from the browser
    body = request.get_json(silent=True)
    if body is None:
        body = {}

    title = body.get("title")
    if title is None:
        title = ""
    title = title.strip()

    if not title:
        abort(400, description="title is required")

    # build the row that will be saved
    db = get_supabase_client()
    payload = {
        "title": title,
        "owner_id": calendar["owner_id"],
        "calendar_ids": [str(calendar["id"])],
        "description": body.get("description") or None,
        "start_timestamp": body.get("start_timestamp") or None,
        "end_timestamp": body.get("end_timestamp") or None,
    }

    result = db.table("events").insert(payload).execute()
    newEventRow = result.data[0]

    # keep the calendar record in sync with this event
    eventId = newEventRow.get("id")
    eventCalendarIds = newEventRow.get("calendar_ids") or []
    Event._addEventToCalendars(eventId, eventCalendarIds)
    return newEventRow, 201


# update an event from a guest editor link
@api_bp.route("/guest/<token>/events/<eventId>", methods=["PUT"])
def guest_edit_event(token, eventId):
    calendar = _get_guest_editor_calendar(token)
    if not calendar:
        abort(403)

    calendarId = str(calendar["id"])
    db = get_supabase_client()

    # make sure the event belongs to this calendar first
    query = db.table("events")
    query = query.select("id")
    query = query.eq("id", eventId)
    query = query.overlaps("calendar_ids", [calendarId])
    query = query.limit(1)
    existingEvent = query.execute()

    if not existingEvent.data:
        abort(404)

    # missing fields get saved as blank values just like before
    body = request.get_json(silent=True)
    if body is None:
        body = {}

    updates = {
        "description": body.get("description") or None,
        "start_timestamp": body.get("start_timestamp") or None,
        "end_timestamp": body.get("end_timestamp") or None,
    }

    title = body.get("title")
    if title is None:
        title = ""
    title = title.strip()

    if title:
        updates["title"] = title

    result = db.table("events").update(updates).eq("id", eventId).execute()
    return result.data[0], 200


# delete an event from a guest editor link
@api_bp.route("/guest/<token>/events/<eventId>", methods=["DELETE"])
def guest_delete_event(token, eventId):
    calendar = _get_guest_editor_calendar(token)
    if not calendar:
        abort(403)

    calendarId = str(calendar["id"])
    db = get_supabase_client()

    # confirm that this calendar has the event
    query = db.table("events")
    query = query.select("id")
    query = query.eq("id", eventId)
    query = query.overlaps("calendar_ids", [calendarId])
    query = query.limit(1)
    existingEvent = query.execute()

    if not existingEvent.data:
        abort(404)

    # load calendar ids before the row is deleted
    fullQuery = db.table("events")
    fullQuery = fullQuery.select("calendar_ids")
    fullQuery = fullQuery.eq("id", eventId)
    fullQuery = fullQuery.limit(1)
    fullResult = fullQuery.execute()

    eventCalendarIds = []
    if fullResult.data:
        eventCalendarIds = fullResult.data[0].get("calendar_ids") or []

    db.table("events").delete().eq("id", eventId).execute()

    # remove the event id from every linked calendar
    Event._removeEventFromCalendars(eventId, eventCalendarIds)
    return "", 204
