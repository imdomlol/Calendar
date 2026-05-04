import os
import subprocess
from flask import abort, redirect, render_template, request, session, url_for
from functools import wraps
from utils.supabase_client import get_supabase_client
from utils.logger import get_logger_client
from datetime import date, datetime
import calendar as pycalendar
from models.user import User


# ========================= Initialization =========================

# get the current build id for the footer
def _compute_build_info():
    # try the Vercel commit sha first
    rawSha = os.environ.get("VERCEL_GIT_COMMIT_SHA")
    if rawSha is None:
        rawSha = ""
    sha = rawSha.strip()

    if sha:
        shortSha = sha[:5]
    else:
        shortSha = ""

    commitDate = ""

    try:
        # ask git for the short sha and date
        gitResult = subprocess.run(
            ["git", "log", "-1", "--format=%h|||%cd", "--date=format:%b %d %Y, %H:%M"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        # only use git output when it worked
        if gitResult.returncode == 0 and gitResult.stdout.strip():
            parts = gitResult.stdout.strip().split("|||", 1)

            if not shortSha:
                shortSha = parts[0]

            if len(parts) > 1:
                commitDate = parts[1]
    except Exception:
        # git may not exist in some deployed places
        pass

    if not shortSha and not commitDate:
        return None

    return {"sha": shortSha, "date": commitDate}


# cache the build info once
buildInfo = _compute_build_info()


# ========================= Auth Helpers =========================


# read the logged in UI user from the Flask session
def _ui_user():
    userData = session.get("ui_user")
    isUserDict = isinstance(userData, dict)

    # make sure this looks like our stored user dict
    if isUserDict and userData.get("id"):
        return userData

    return None


# ========================= Auth Decorators =========================


# protect a UI route from users who are not logged in
def ui_login_required(viewFunc):
    # keep the original route function info for Flask
    @wraps(viewFunc)
    def wrapped(*args, **kwargs):
        if not _ui_user():
            return redirect(url_for("ui.login", next=request.path))

        return viewFunc(*args, **kwargs)

    return wrapped


# protect a UI route so only admins can use it
def ui_admin_required(viewFunc):
    @wraps(viewFunc)
    def wrapped(*args, **kwargs):
        userData = _ui_user()
        if not userData:
            return redirect(url_for("ui.login", next=request.path))

        # admins are marked in our users table
        if not userData.get("is_admin"):
            abort(403)

        return viewFunc(*args, **kwargs)

    return wrapped


# ========================= Error Handling =========================


# turn a Supabase login error into text for the page
def _format_login_error(exception):
    rawMessage = getattr(exception, "message", None)

    if not rawMessage:
        rawMessage = str(exception)

    if not rawMessage:
        rawMessage = ""
    message = rawMessage.strip()

    rawCode = getattr(exception, "code", None)

    if rawCode is None:
        rawCode = ""
    code = rawCode.strip()

    # lowercase the message so matching is easier
    normalMessage = message.lower()

    if "email not confirmed" in normalMessage or code == "email_not_confirmed":
        return "Your account is not verified yet. Check your email for the verification link and try again."

    if code:
        return f"Login failed: {message} (code: {code})"

    return "There was an issue, please try again."


# ========================= URL and OAuth Helpers =========================


# get the current app base URL
def _resolve_app_base_url():
    return request.url_root.rstrip("/")


# read the Google OAuth client settings
def _google_oauth_config():
    rawId = os.environ.get("GOOGLE_CLIENT_ID")
    if rawId is None:
        rawId = ""
    clientId = rawId.strip()

    rawSecret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if rawSecret is None:
        rawSecret = ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret


# read the Microsoft OAuth client settings
def _outlook_oauth_config():
    rawId = os.environ.get("MS_CLIENT_ID")
    if rawId is None:
        rawId = ""
    clientId = rawId.strip()

    rawSecret = os.environ.get("MS_CLIENT_SECRET")
    if rawSecret is None:
        rawSecret = ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret


# ========================= Navigation =========================


# build the main feature navigation links
def features_nav():
    return [
        {"label": "Calendars", "href": url_for("ui.manage_calendars")},
        {"label": "Events", "href": url_for("ui.manage_events")},
        {"label": "Friends", "href": url_for("ui.manage_friends")},
    ]


# ========================= Calendar Helper =========================


# build the month preview data for the home page
def build_month_preview_data(eventsForCalendar):
    today = date.today()
    year = today.year
    month = today.month

    # count events by day number
    evtCounts = {}
    for event in eventsForCalendar:
        timestamp = event.get("start_timestamp")
        if timestamp is None:
            timestamp = ""
        rawTimestamp = str(timestamp)

        try:
            # parse only the date and time part
            eventDate = datetime.fromisoformat(rawTimestamp[:19])
        except ValueError:
            continue

        # only count events in the current month
        if eventDate.year == year and eventDate.month == month:
            if eventDate.day in evtCounts:
                evtCounts[eventDate.day] = evtCounts[eventDate.day] + 1
            else:
                evtCounts[eventDate.day] = 1

    # turn the calendar rows into template data
    weeks = []
    for week in pycalendar.monthcalendar(year, month):
        row = []
        for dayNumber in week:
            if dayNumber != 0:
                dayValue = dayNumber
            else:
                dayValue = None

            if dayNumber in evtCounts:
                dayCount = evtCounts[dayNumber]
            else:
                dayCount = 0

            row.append({"day": dayValue, "count": dayCount})
        weeks.append(row)

    return {
        "month_label": f"{pycalendar.month_name[month]} {year}",
        "weeks": weeks,
    }

# ========================= Rendering =========================


# render a template with the shared page title
def render_page(title, template, **pageContext):
    return render_template(template, title=title, **pageContext)


# ========================= User Helpers =========================


# make a User model from the session user
def _make_ui_user() -> User:
    userData = _ui_user()

    if "display_name" in userData:
        displayName = userData["display_name"]
    else:
        displayName = ""

    return User(
        userId=userData["id"],
        displayName=displayName,
    )


# resolve an email or id into a user id
def resolve_member_id(value: str):
    db = get_supabase_client()

    if "@" in value:
        result = db.table("users").select("id").eq("email", value).limit(1).execute()

        if result.data:
            return result.data[0]["id"]

        return None

    return value


# ========================= Context Processor =========================


# keep this import low to avoid a circular import
from api.ui_routes import ui_bp  # noqa: E402


# add globals that every UI template can use
@ui_bp.context_processor
def _inject_globals():
    activeMessage = None

    try:
        # use the logger client so user auth does not block this read
        db = get_logger_client() or get_supabase_client()

        notificationTable = db.table("notifications")
        notificationQuery = notificationTable.select("message")
        activeQuery = notificationQuery.eq("active", True)
        orderedQuery = activeQuery.order("created_at", desc=True)
        limitedQuery = orderedQuery.limit(1)
        result = limitedQuery.execute()

        if result.data:
            firstRow = result.data[0]

            if "message" in firstRow:
                activeMessage = firstRow["message"]
            else:
                activeMessage = None
    except Exception:
        # ignore notification errors so pages can still load
        activeMessage = None

    # send the common template values back to Flask
    return {
        "ui_user": _ui_user(),
        "features_nav": features_nav(),
        "build_info": buildInfo,
        "active_message": activeMessage,
    }
