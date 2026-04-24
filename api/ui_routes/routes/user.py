from flask import redirect, request, url_for, jsonify
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


@ui_bp.route("/me/token")
@ui_login_required
def get_token():
    token = _ui_user().get("access_token")
    return jsonify({"token": token})


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
