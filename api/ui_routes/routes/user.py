import secrets
from datetime import datetime, timedelta
from flask import redirect, request, url_for, jsonify
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    render_page,
    ui_login_required,
    _resolve_app_base_url,
    resolve_member_id,
)
from models.calendar import Calendar
from models.event import Event
from models.external import External
from utils.supabase_client import get_supabase_client


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    providersList = []
    try:
        u = _make_ui_user()
        providersList = u.listExternals()
    except Exception as e:
        status = "error"
        message = f"Couldn't load external connections: {e}"
    return render_page(
        "Manage Externals", "user/externals.html",
        providers=providersList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    records = []
    try:
        u = _make_ui_user()
        records = u.listCalendars()
    except Exception as e:
        status = "error"
        message = f"Couldn't load calendars: {e}"
    return render_page(
        "Manage Calendars", "user/calendars.html",
        status=status,
        message=message,
        owner_id=_ui_user()["id"],
        calendars=records,
        has_guest_link_fields=True,
        app_base_url=_resolve_app_base_url(),
    )


@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    calendars = []
    events = []
    try:
        u = _make_ui_user()
        calendars = u.listCalendars()
        if calendars:
            selected_calendar = next(
                (c for c in calendars if str(c.get("id")) == selected_calendar_id),
                calendars[0],
            )
            selected_calendar_id = str(selected_calendar.get("id"))
            events = Calendar.listEvents(selected_calendar_id)
    except Exception as err:
        status = "error"
        message = f"Couldn't load events: {err}"
    if not calendars:
        return render_page("Manage Events", "user/events_no_calendars.html",
                           status=status, message=message)
    now = datetime.now()
    default_start = now.strftime("%Y-%m-%dT%H:%M")
    default_end = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    return render_page(
        "Manage Events", "user/events.html",
        status=status,
        message=message,
        calendars=calendars,
        selected_calendar_id=selected_calendar_id,
        events=events,
        default_start=default_start,
        default_end=default_end,
    )


@ui_bp.route("/user/events/<event_id>/edit")
@ui_login_required
def edit_event(event_id):
    uid = _ui_user()["id"]
    event = Event.find(event_id)
    if not event or event.get("owner_id") != uid:
        return redirect(url_for("ui.manage_events", status="error", message=f"Event {event_id} not found"))
    return render_page(
        "Edit Event", "user/events_edit.html",
        event=event,
        status="",
        message="",
    )


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    friendsList = []
    try:
        u = _make_ui_user()
        friendsList = u.listFriendsData()
    except Exception as e:
        status = "error"
        message = f"Couldn't load friends: {e}"
    return render_page(
        "Manage Friends", "user/friends.html",
        friends=friendsList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    return render_page("Remove Account", "user/remove_account.html")


@ui_bp.route("/user/events", methods=["POST"])
@ui_login_required
def create_event():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendarIds = body.get("calendar_ids", [])
    if not title or not calendarIds:
        return jsonify({"error": "title and calendar_ids are required"}), 400
    user = _make_ui_user()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in calendarIds):
        return jsonify({"error": "not authorized for any of the given calendars"}), 403
    event = Event(
        title=title,
        calendarIds=calendarIds,
        ownerId=user.userId,
        description=body.get("description"),
        startTimestamp=body.get("start_timestamp"),
        endTimestamp=body.get("end_timestamp"),
    )
    result = event.save()
    return jsonify(result.data[0]), 201


@ui_bp.route("/user/events/<event_id>", methods=["PUT"])
@ui_login_required
def update_event(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        return jsonify({"error": "event not found"}), 404
    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        return jsonify({"error": "not authorized to edit this event"}), 403
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    description = body.get("description")
    startTimestamp = body.get("start_timestamp")
    endTimestamp = body.get("end_timestamp")
    calendarIds = body.get("calendar_ids")
    if all(v is None for v in [title, description, startTimestamp, endTimestamp, calendarIds]):
        return jsonify({"error": "no fields to update"}), 400
    event = Event(title=eventData["title"], calendarIds=eventData["calendar_ids"], ownerId=eventData["owner_id"])
    event.id = event_id
    editResult = event.edit(
        title=title,
        description=description,
        startTimestamp=startTimestamp,
        endTimestamp=endTimestamp,
        calendarIds=calendarIds,
    )
    return jsonify(editResult.data[0]), 200


@ui_bp.route("/user/events/<event_id>", methods=["DELETE"])
@ui_login_required
def delete_event(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        return jsonify({"error": "event not found"}), 404
    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        return jsonify({"error": "not authorized to delete this event"}), 403
    event = Event(title=eventData["title"], calendarIds=eventData["calendar_ids"])
    event.id = event_id
    event.remove()
    return "", 204


@ui_bp.route("/user/calendars", methods=["POST"])
@ui_login_required
def create_calendar():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    uid = _ui_user()["id"]
    cal = Calendar(name=name, ownerId=uid)
    result = cal.save()
    return jsonify(result.data[0]), 201


@ui_bp.route("/user/calendars/<calendar_id>", methods=["DELETE"])
@ui_login_required
def delete_calendar(calendar_id):
    db = get_supabase_client()
    uid = _ui_user()["id"]
    existing = db.table("calendars").select("id", "name", "owner_id").eq("id", calendar_id).eq("owner_id", uid).execute()
    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404
    calData = existing.data[0]
    cal = Calendar(name=calData["name"], ownerId=calData["owner_id"])
    cal.id = calendar_id
    cal.remove()
    return "", 204


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["POST"])
@ui_login_required
def create_guest_link(calendar_id):
    db = get_supabase_client()
    uid = _ui_user()["id"]
    existing = db.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", uid).execute()
    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404
    body = request.get_json(silent=True) or {}
    role = body.get("role", "viewer")
    if role not in ("viewer", "editor"):
        return jsonify({"error": "role must be viewer or editor"}), 400
    token = secrets.token_urlsafe(32)
    result = db.table("calendars").update({
        "guest_link_token": token,
        "guest_link_role": role,
        "guest_link_active": True,
    }).eq("id", calendar_id).execute()
    return jsonify(result.data[0]), 200


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["DELETE"])
@ui_login_required
def revoke_guest_link(calendar_id):
    db = get_supabase_client()
    uid = _ui_user()["id"]
    existing = db.table("calendars").select("id").eq("id", calendar_id).eq("owner_id", uid).execute()
    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404
    db.table("calendars").update({
        "guest_link_token": None,
        "guest_link_role": None,
        "guest_link_active": False,
    }).eq("id", calendar_id).execute()
    return "", 204


@ui_bp.route("/user/friends", methods=["POST"])
@ui_login_required
def add_friend():
    body = request.get_json(silent=True) or {}
    user = _make_ui_user()
    try:
        friends = user.addFriend(friendId=body.get("friend_id"), email=body.get("email"), value=body.get("value"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"friends": friends})


@ui_bp.route("/user/friends/<friend_id>", methods=["DELETE"])
@ui_login_required
def remove_friend(friend_id):
    user = _make_ui_user()
    try:
        user.removeFriend(friend_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return "", 204


@ui_bp.route("/user/me", methods=["DELETE"])
@ui_login_required
def delete_me():
    user = _make_ui_user()
    user.removeAccount()
    return "", 204


@ui_bp.route("/calendars/<calendar_id>/members", methods=["POST"])
@ui_login_required
def add_calendar_member(calendar_id):
    db = get_supabase_client()
    uid = _ui_user()["id"]
    existing = db.table("calendars").select("id, name, owner_id, member_ids").eq("id", calendar_id).eq("owner_id", uid).execute()
    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404
    body = request.get_json(silent=True) or {}
    value = (body.get("member") or "").strip()
    if not value:
        return jsonify({"error": "member is required"}), 400
    member_id = resolve_member_id(value)
    if not member_id:
        return jsonify({"error": "no user found with that email"}), 404
    cal_data = existing.data[0]
    cal = Calendar(name=cal_data["name"], ownerId=cal_data["owner_id"])
    cal.id = calendar_id
    cal.memberIds = cal_data.get("member_ids") or [cal_data["owner_id"]]
    try:
        cal.add_member(member_id)
    except (ValueError, Exception) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True}), 200


@ui_bp.route("/settings/external/<external_id>", methods=["DELETE"])
@ui_login_required
def disconnect_external(external_id):
    uid = _ui_user()["id"]
    db = get_supabase_client()
    ext = External(id=external_id, supabaseClient=db, userId=uid)
    try:
        ext.remove(external_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return "", 204
