# home and dashboard routes; the root route renders a month-preview calendar for logged-in users
from flask import redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    _ui_user,
    admin_nav,
    build_month_preview_data,
    guest_nav,
    placeholder_calendars,
    placeholder_events,
    render_page,
    user_nav,
)


# main landing route; shows a guest page if not logged in, or a month preview calendar if logged in
@ui_bp.route("/")
def home():
    user = _ui_user()

    if not user:
        return render_page("Calendar Info System", "guest", guest_nav(), "home/guest.html")

    user_id = user.get("id")
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status_message = ""
    calendars = []
    selected_calendar = None
    events_for_calendar = []

    try:
        supabase = _get_ui_supabase_client()
        calendars_result = (
            supabase.table("calendars")
            .select("id, name, owner_id")
            .eq("owner_id", user_id)
            .order("age_timestamp", desc=False)
            .execute()
        )
        calendars = calendars_result.data or []

        if calendars:
            # fall back to the first calendar if the requested id is missing or invalid
            selected_calendar = next(
                (c for c in calendars if str(c.get("id")) == selected_calendar_id),
                calendars[0],
            )
            selected_calendar_id = str(selected_calendar.get("id"))

            events_result = (
                supabase.table("events")
                .select("id, title, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events_for_calendar = events_result.data or []
    except Exception as exc:
        status_message = f"Could not load calendars: {exc}"

    if not calendars:
        return render_page("Calendar Home", "user", user_nav(), "home/no_calendars.html",
                           status_message=status_message)

    calendar_data = build_month_preview_data(events_for_calendar)
    calendar_name = selected_calendar.get("name") or "Untitled Calendar"

    return render_page("Calendar Home", "user", user_nav(), "home/calendar.html",
                       calendars=calendars,
                       selected_calendar_id=selected_calendar_id,
                       calendar_name=calendar_name,
                       calendar_data=calendar_data,
                       status_message=status_message)


@ui_bp.route("/home")
def brand_home():
    return redirect(url_for("ui.home"))


# TODO: view_calendars and view_events are stubs not yet wired to real queries
@ui_bp.route("/calendars")
def view_calendars():
    return render_page("View Calendars", "guest", guest_nav(), "home/view_calendars.html",
                       calendars=placeholder_calendars)


@ui_bp.route("/events")
def view_events():
    return render_page("View Events", "guest", guest_nav(), "home/view_events.html",
                       events=placeholder_events)


# role can be "user", "admin", or anything else; "user" and "admin" require login
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
        role=role,
    )
