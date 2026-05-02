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

# this function runs once when the server starts
# it tries to figure out what git commit is currently deployed
def _compute_build_info():
    # try to get the git commit sha from the vercel env var
    rawSha = os.environ.get("VERCEL_GIT_COMMIT_SHA")
    if rawSha is None:
        rawSha = ""
    sha = rawSha.strip()

    # the full sha is really long and we just need enough to identify the build
    if sha:
        shortSha = sha[:5]
    else:
        shortSha = ""
    commitDate = ""

    try:
        # run git log to get the short sha and the commit date
        # the timeout is 2 seconds so we dont hang the server if github is slow
        res = subprocess.run(
            ["git", "log", "-1", "--format=%h|||%cd", "--date=format:%b %d %Y, %H:%M"],
            capture_output=True, text=True, timeout=2,
        )
        # check if the command worked and gave us something back
        if res.returncode == 0 and res.stdout.strip():
            # split on ||| to get the sha and date as separate parts
            parts = res.stdout.strip().split("|||", 1)
            # only use the git sha if we didnt already get one from vercel
            if not shortSha:
                shortSha = parts[0]
            if len(parts) > 1:
                commitDate = parts[1]
    except Exception:
        # if git is not available or something goes wrong we just go next
        pass

    if not shortSha and not commitDate:
        return None
    return {"sha": shortSha, "date": commitDate}

# we cache it here so we dont have to run git every single request
buildInfo = _compute_build_info()

# ========================= Auth Helpers =========================

# this function checks if there is a logged in user in the current session
# Flask sessions are like a little storage area attached to each browser visit
def _ui_user():
    # get the user dict from the flask session
    # session.get returns None if the key doesnt exist
    usr = session.get("ui_user")
    isDict = isinstance(usr, dict)

    # if its a dict and has an id then its a valid user
    if isDict == True and usr.get("id"):
        return usr
    
    # no user is logged in
    return None

# ========================= Auth Decorators =========================

# this function is a decorator
# you put @ui_login_required above a route function to protect it
# if the user is not logged in they get sent to the login page instead of seeing the page
def ui_login_required(viewFn):
    # we use wraps so the original function name and metadata are preserved
    # without wraps Flask would get confused about the function names
    @wraps(viewFn)
    def wrapped(*args, **kwargs):

        if not _ui_user():
            # no user so send them to login
            return redirect(url_for("ui.login", next=request.path))

        # user is logged in so call the actual view function and return its result
        return viewFn(*args, **kwargs)
    return wrapped

# you put @ui_admin_required above admin only routes
def ui_admin_required(viewFn):
    # we use wraps to preserve the original function info just like in ui_login_required
    @wraps(viewFn)
    def wrapped(*args, **kwargs):
        # first check if they are logged in at all
        usr = _ui_user()
        if not usr:
            # not logged in so send them to the login page
            return redirect(url_for("ui.login", next=request.path))

        # is_admin is set from the is_admin column in the custom users table in Supabase (not the built in one)
        if not usr.get("is_admin"):
            # they are logged in but not an admin
            abort(403)

        # they are logged in and they are an admin
        return viewFn(*args, **kwargs)
    return wrapped


# ========================= Error Handling =========================

# this function takes a Supabase login error and makes it readable
def _format_login_error(exception):
    # Supabase exceptions sometimes have a message attribute instead of just str()
    rawMsg = getattr(exception, "message", None)

    # if there was no message attribute fall back to converting the exception to a string
    if not rawMsg:
        rawMsg = str(exception)

    # if that is also empty just use an empty string
    if not rawMsg:
        rawMsg = ""
    msg = rawMsg.strip()

    # pull the error code out of the exception the same way we pulled the message
    rawCode = getattr(exception, "code", None)

    if rawCode is None:
        rawCode = ""
    code = rawCode.strip()

    # set the message to lowercase so we can compare it without worrying about uppercase / lowercase
    norm = msg.lower()

    # check if the error is about email not being confirmed
    if "email not confirmed" in norm or code == "email_not_confirmed":
        return "Your account is not verified yet. Check your email for the verification link and try again."

    # if there is a code include it in the message so we can see
    if code:
        return f"Login failed: {msg} (code: {code})"

    # if nothing else matched just show a generic error
    return "There was an issue, please try again."


# ========================= URL and OAuth Helpers =========================

# this function figures out what the base URL of the app is
# we need this to build full URLs for things like Google OAuth redirects
def _resolve_app_base_url():
    return request.url_root.rstrip("/")


# this function reads the Google OAuth client credentials from environment variables
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


# this function works the same as _google_oauth_config but for Microsoft
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
def features_nav():
    return [
            {"label": "Calendars", "href": url_for("ui.manage_calendars")},
            {"label": "Events", "href": url_for("ui.manage_events")},
            {"label": "Friends", "href": url_for("ui.manage_friends")},
    ]

# ========================= Calendar Helper =========================

# this function builds the data needed to show a mini calendar grid for the current month
# it figures out which days have events on them so we can show dots or counts on those days
# it gives back a dict with a label like "May 2026" and a list of weeks
# each week is a list of dicts with the day number and how many events are on that day
def build_month_preview_data(eventsForCalendar):
    today = date.today()
    year = today.year
    month = today.month

    # evtCounts is a dict where the key is the day number like 1 through 31 and the value is how many events are on that day
    evtCounts = {}
    for event in eventsForCalendar:
        # event.get returns None if the key is missing so we replace it with an empty string
        ts = event.get("start_timestamp")
        if ts is None:
            ts = ""
        raw = str(ts)
        try:
            # parse the timestamp string into a datetime object
            # a typical timestamp looks like 2026-05-02T14:30:00+00:00 and we grab up to the seconds
            dt = datetime.fromisoformat(raw[:19])
        except ValueError:
            # if the timestamp is not in a valid format we just skip this event
            continue

        # we only want to count events that belong to the month we are showing
        if dt.year == year and dt.month == month:
            if dt.day in evtCounts:
                evtCounts[dt.day] = evtCounts[dt.day] + 1
            else:
                evtCounts[dt.day] = 1

    # pycalendar.monthcalendar gives us a list of weeks where each week is a list of 7 day numbers
    weeks = []
    for week in pycalendar.monthcalendar(year, month):
        row = []
        for d in week:
            # pycalendar uses 0 for days that are outside the current month
            # we convert those to None so the template can show blank cells
            if d != 0:
                dayVal = d
            else:
                dayVal = None

            # if the day number is not in evtCounts it means zero events happened on that day
            if d in evtCounts:
                dayCount = evtCounts[d]
            else:
                dayCount = 0
            row.append({"day": dayVal, "count": dayCount})
        weeks.append(row)

    # give back the finished structure with a human readable month label and the weeks grid
    return {
        "month_label": f"{pycalendar.month_name[month]} {year}",
        "weeks": weeks,
    }

# ========================= Rendering =========================

# this is a wrapper around render_template that makes sure we always pass the same standard stuff
# ctx is a special python thing that captures any extra keyword arguments and passes them along
# it gives back the rendered HTML string from the template
def render_page(title, template, **ctx):
    return render_template(template, title=title, **ctx)

# ========================= User Helpers =========================

# this function creates a User model object from the current session user
# we use this when we need to call methods on the User class like saving or fetching data
def _make_ui_user() -> User:
    usr = _ui_user()

    # if the key does not exist we fall back to an empty string
    if "display_name" in usr:
        displayName = usr["display_name"]
    else:
        displayName = ""

    # create a User object
    return User(
        userId=usr["id"],
        displayName=displayName,
    )


# this function takes either a user id or an email address and always gives back a user id
def resolve_member_id(value: str):
    db = get_supabase_client()

    # the @ symbol is what makes something an email address
    if "@" in value:
        # query the users table to find the id that matches this email
        result = db.table("users").select("id").eq("email", value).limit(1).execute()

        if result.data:
            return result.data[0]["id"]
        # no user found with that email so give back None
        return None
    # if it was not an email then assume it is already a user id and just give it back
    return value


# ========================= Context Processor =========================

# this import is down here because putting it at the top would cause a circular import error
from api.ui_routes import ui_bp  # noqa: E402


# this is a Flask context processor which means Flask calls it before rendering any template
# it injects variables so every template automatically has access to them
@ui_bp.context_processor
def _inject_globals():
    # if there is no active admin notification set this to None
    activeMsg = None
    try:
        # we use the logger client here instead of the regular Supabase client
        # this is because sign_in_with_password changes the shared client session to the users JWT
        # which causes Supabase RLS to block this notifications read on later requests
        db = get_logger_client() or get_supabase_client()
        
        # we want the newest one so we order by created_at descending
        result = (
            db.table("notifications")
            .select("message")
            .eq("active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        # if we got a result back grab the message text from the first row
        if result.data:
            firstRow = result.data[0]
            # check that the message key actually exists before reading it
            if "message" in firstRow:
                activeMsg = firstRow["message"]
            else:
                activeMsg = None
    except Exception:
        # if anything goes wrong with the database we just ignore announcements
        activeMsg = None

    # return a dict of values that every template can now access directly
    return {
        "ui_user": _ui_user(),          # ui_user is the current logged in user
        "features_nav": features_nav(), # features_nav is the list of nav links for the hamburger menu
        "build_info": buildInfo,        # build_info is the id shown in the footer
        "active_message": activeMsg,    # active_message is the current system wide notification
    }
