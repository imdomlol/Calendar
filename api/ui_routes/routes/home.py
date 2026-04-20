from flask import redirect, request, url_for
from api.ui_routes import ui_bp

from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    _ui_user,
    admin_nav,
    guest_nav,
    render_page,
    ui_login_required,
    user_nav,
)
from api.ui_routes.helpers import build_month_preview_data, placeholder_calendars, placeholder_events


# main landing route
@ui_bp.route("/")
def home():
    user = _ui_user()

    if not user:
        return render_page("Calendar Info System", "guest", guest_nav(), "home/guest.html")

    userId = user.get("id")
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    calendars = []
    selected_calendar = None
    events_for_calendar = []

    try:
        supabase = _get_ui_supabase_client()
        calendars_result = (
            supabase.table("calendars")
            .select("id, name, owner_id")
            .eq("owner_id", userId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        calendars = calendars_result.data or []

        if calendars:
            # loop through calendars to find the selected one
            # if we cant find it we fall back to the first one
            selected_calendar = None
            for c in calendars:
                if str(c.get("id")) == selected_calendar_id:
                    selected_calendar = c
                    break
            if selected_calendar is None:
                selected_calendar = calendars[0]
            selected_calendar_id = str(selected_calendar.get("id"))

            events_result = (
                supabase.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events_for_calendar = events_result.data or []
    except Exception as exc:
        status = "error"
        message = f"Could not load calendars: {exc}"

    if not calendars:
        return render_page("Calendar Home", "user", user_nav(), "home/no_calendars.html",
                           status=status, message=message)

    calendar_name = selected_calendar.get("name") or "Untitled Calendar"

    return render_page("Calendar Home", "user", user_nav(), "home/calendar.html",
                       calendars=calendars,
                       selected_calendar_id=selected_calendar_id,
                       calendar_name=calendar_name,
                       events=events_for_calendar,
                       status=status,
                       message=message)



@ui_bp.route("/home")
def brand_home():
    # this handles the /home url
    # some users might try /home instead of /
    # we just redirect them to the actual home page
    # url_for gives us the url for the home function
    homeUrl = url_for("ui.home") #get home url
    # redirect the browser there
    return redirect(homeUrl)

@ui_bp.route("/calendars")
def view_calendars():
    cals = placeholder_calendars #placeholder data for now
    return render_page("View Calendars", "guest", guest_nav(), "home/view_calendars.html",
                       calendars=cals)


@ui_bp.route("/events")
def view_events():
    return render_page("View Events", "guest", guest_nav(), "home/view_events.html",
                       events=placeholder_events)




@ui_bp.route("/dashboard/<role>")
def dashboard(role):
    if role in {"user", "admin"} and not _ui_user():
        return redirect(url_for("ui.login", next=request.path))

    # pick nav based on role
    nav = admin_nav() if role == "admin" else user_nav()
    return render_page(
        "Admin Dashboard" if role == "admin" else "User Dashboard",
        role,
        nav,
        "home/dashboard.html",
        role=role,
    )
