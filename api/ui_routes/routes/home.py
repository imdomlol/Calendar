from flask import redirect, request, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _get_ui_supabase_client,
    render_page,
    user_nav,
    admin_nav,
    guest_nav,
    ui_login_required,
)
from api.ui_routes.helpers import build_month_preview_data, placeholder_calendars, placeholder_events


# main landing route
@ui_bp.route("/")
def home():
    # get the user from the session
    user = _ui_user()

    # if not logged in send them to the login page
    if not user:
        return redirect(url_for("ui.login", next=request.path))

    # get the user id so we can query their data
    userId = user.get("id")
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    # these will get filled in below
    calendars = []
    selected_calendar = None
    events_for_calendar = []

    try:
        calDb = _get_ui_supabase_client()
        # get all calendars owned by this user
        calendars_result = (
            calDb.table("calendars")
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

            # get events for the selected calendar
            events_result = (
                calDb.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events_for_calendar = events_result.data or []
    except Exception as e:
        status = "error"
        message = f"Couldn't load calendars for uid {userId}: {e}"

    # if the user has no calendars show the no calendars page
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
    # show the public calendars page
    # uses placeholder data for now
    cals = placeholder_calendars #placeholder data for now
    return render_page("View Calendars", "guest", guest_nav(), "home/view_calendars.html",
                       calendars=cals)



@ui_bp.route("/events")
def view_events():
    # show the public events page
    # also placeholder data
    return render_page("View Events", "guest", guest_nav(), "home/view_events.html",
                       events=placeholder_events)




@ui_bp.route("/dashboard/<role>")
def dashboard(role):
    # if a logged in role is requested make sure the user is actually logged in
    if role in {"user", "admin"} and not _ui_user():
        return redirect(url_for("ui.login", next=request.path))

    # pick nav based on role
    # admin gets the admin nav and everyone else gets user nav
    nav = admin_nav() if role == "admin" else user_nav()
    return render_page(
        "Admin Dashboard" if role == "admin" else "User Dashboard",
        role,
        nav,
        "home/dashboard.html",
        role=role,
    )
