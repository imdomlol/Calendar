from flask import redirect, request, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    render_page,
    user_nav,
    admin_nav,
    ui_login_required,
)
from models.calendar import Calendar


@ui_bp.route("/")
def home():
    user = _ui_user()
    if not user:
        return redirect(url_for("ui.login", next=request.path))

    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    calendars = []
    events_for_calendar = []

    try:
        u = _make_ui_user()
        calendars = u.listCalendars()
    except Exception as e:
        status = "error"
        message = f"Couldn't load calendars: {e}"

    if not calendars:
        return render_page("Calendar Home", "user", user_nav(), "home/no_calendars.html",
                           status=status, message=message)

    selected_calendar = next(
        (c for c in calendars if str(c.get("id")) == selected_calendar_id),
        calendars[0],
    )
    selected_calendar_id = str(selected_calendar.get("id"))

    try:
        events_for_calendar = Calendar.listEvents(selected_calendar_id)
    except Exception as e:
        if not status:
            status = "error"
            message = f"Couldn't load events: {e}"

    return render_page(
        "Calendar Home", "user", user_nav(), "home/calendar.html",
        calendars=calendars,
        selected_calendar_id=selected_calendar_id,
        calendar_name=selected_calendar.get("name") or "Untitled Calendar",
        events=events_for_calendar,
        status=status,
        message=message,
    )


@ui_bp.route("/home")
def brand_home():
    return redirect(url_for("ui.home"))


@ui_bp.route("/dashboard/<role>")
def dashboard(role):
    if role in {"user", "admin"} and not _ui_user():
        return redirect(url_for("ui.login", next=request.path))
    nav = admin_nav() if role == "admin" else user_nav()
    return render_page(
        "Admin Dashboard" if role == "admin" else "User Dashboard",
        role,
        nav,
        "home/dashboard.html",
    )
