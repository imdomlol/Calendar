import secrets
from flask import abort, redirect, request, url_for, jsonify
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    render_page,
    ui_login_required,
    user_nav,
    _resolve_app_base_url,
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
        "Manage Externals", "user", user_nav(), "user/externals.html",
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
        "Manage Calendars", "user", user_nav(), "user/calendars.html",
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
        return render_page("Manage Events", "user", user_nav(), "user/events_no_calendars.html",
                           status=status, message=message)
    return render_page(
        "Manage Events", "user", user_nav(), "user/events.html",
        status=status,
        message=message,
        calendars=calendars,
        selected_calendar_id=selected_calendar_id,
        events=events,
    )


@ui_bp.route("/user/events/<event_id>/edit")
@ui_login_required
def edit_event(event_id):
    uid = _ui_user()["id"]
    u = _make_ui_user()
    rows = u.viewEvent(event_id)
    if not rows or rows[0].get("owner_id") != uid:
        return redirect(url_for("ui.manage_events", status="error", message=f"Event {event_id} not found"))
    return render_page(
        "Edit Event", "user", user_nav(), "user/events_edit.html",
        event=rows[0],
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
        "Manage Friends", "user", user_nav(), "user/friends.html",
        friends=friendsList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")


@ui_bp.route("/user/events", methods=["POST"])
@ui_login_required
def create_event():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    calendarIds = body.get("calendar_ids", [])
    if not title or not calendarIds:
        abort(400)
    user = _make_ui_user()
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
    return jsonify(result.data[0]), 201


@ui_bp.route("/user/events/<event_id>", methods=["PUT"])
@ui_login_required
def update_event(event_id):
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()
    if not result.data:
        abort(404)
    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        abort(403)
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    description = body.get("description")
    startTimestamp = body.get("start_timestamp")
    endTimestamp = body.get("end_timestamp")
    calendarIds = body.get("calendar_ids")
    if all(v is None for v in [title, description, startTimestamp, endTimestamp, calendarIds]):
        abort(400)
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
        abort(404)
    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = [cal["id"] for cal in user.listCalendars()]
    if not any(cid in userCalIds for cid in eventData.get("calendar_ids", [])):
        abort(403)
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
        abort(400)
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
        abort(404)
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
        abort(404)
    body = request.get_json(silent=True) or {}
    role = body.get("role", "viewer")
    if role not in ("viewer", "editor"):
        abort(400)
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
        abort(404)
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
        friends = user.addFriend(friendId=body.get("friend_id"), email=body.get("email"))
    except ValueError:
        abort(400)
    return jsonify({"friends": friends})


@ui_bp.route("/user/friends/<friend_id>", methods=["DELETE"])
@ui_login_required
def remove_friend(friend_id):
    user = _make_ui_user()
    try:
        user.removeFriend(friend_id)
    except ValueError:
        abort(404)
    return "", 204


@ui_bp.route("/user/me", methods=["DELETE"])
@ui_login_required
def delete_me():
    user = _make_ui_user()
    user.removeAccount()
    return "", 204


@ui_bp.route("/settings/external/<external_id>", methods=["DELETE"])
@ui_login_required
def disconnect_external(external_id):
    uid = _ui_user()["id"]
    db = get_supabase_client()
    ext = External(id=external_id, url="", provider="", supabaseClient=db, userId=uid)
    try:
        ext.remove(external_id)
    except ValueError:
        abort(404)
    return "", 204
