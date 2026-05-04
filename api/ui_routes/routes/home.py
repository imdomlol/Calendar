from flask import redirect, request, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    render_page,
)
from models.calendar import Calendar


# ========================= Home Routes =========================

# main calendar home page, loads calendars and events for the selected one
@ui_bp.route("/")
def home():
    # make sure the user is logged in
    user = _ui_user()
    if not user:
        return redirect(url_for("ui.login", next=request.path))

    # read query params from the URL
    selectedCalendarId = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    calendars = []
    eventsForCalendar = []

    # try loading all calendars the user has access to
    try:
        uiUser = _make_ui_user()
        calendars = uiUser.list_calendars()
    except Exception as e:
        status = "error"
        message = f"Couldn't load calendars: {e}"

    # if there are no calendars, show the empty state page
    if not calendars:
        return render_page(
            "Calendar Home",
            "home/no_calendars.html",
            status=status,
            message=message,
        )

    # find the calendar matching the id in the URL, fall back to the first one
    selectedCalendar = calendars[0]
    for cal in calendars:
        if str(cal.get("id")) == selectedCalendarId:
            selectedCalendar = cal
            break

    # lock in the id in case we fell back to the default calendar
    selectedCalendarId = str(selectedCalendar.get("id"))

    # load events for whichever calendar is selected
    try:
        eventsForCalendar = Calendar.list_events(selectedCalendarId)
    except Exception as e:
        if not status:
            status = "error"
            message = f"Couldn't load events: {e}"

    # use a fallback name if the calendar has no name set
    calName = selectedCalendar.get("name")
    if not calName:
        calName = "Untitled Calendar"

    return render_page(
        "Calendar Home",
        "home/calendar.html",
        calendars=calendars,
        selected_calendar_id=selectedCalendarId,
        calendar_name=calName,
        events=eventsForCalendar,
        status=status,
        message=message,
    )


# ========================= Redirect Routes =========================

# /home just bounces to the root home route
@ui_bp.route("/home")
def brand_home():
    return redirect(url_for("ui.home"))


# admin dashboard page, checks login then renders the template
@ui_bp.route("/dashboard/admin")
def dashboard():
    if not _ui_user():
        return redirect(url_for("ui.login", next=request.path))
    return render_page("Admin Dashboard", "home/dashboard.html")
