import os
import subprocess
from flask import redirect, render_template, request, session, url_for
from functools import wraps
from utils.supabase_client import get_supabase_client
from datetime import date, datetime
import calendar as pycalendar


def _compute_build_info():
    # try to get the git commit sha from the vercel env var
    sha = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "").strip()
    shortSha = sha[:7] if sha else ""
    commitDate = ""

    try:
        # run git log to get the short sha and the commit date
        # format string splits them with ||| so we can split later
        res = subprocess.run(
            ["git", "log", "-1", "--format=%h|||%cd", "--date=format:%b %d %Y, %H:%M"],
            capture_output=True, text=True, timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split("|||", 1)
            # only use git sha if we didnt get one from vercel
            if not shortSha:
                shortSha = parts[0]
            if len(parts) > 1:
                commitDate = parts[1]
    except Exception:
        pass

    # if we have nothing return None
    if not shortSha and not commitDate:
        return None
    # return a dict with the sha and date
    return {"sha": shortSha, "date": commitDate}


BUILD_INFO = _compute_build_info()


placeholder_calendars = [
    {"id": 1, "name": "Work Calendar", "owner": "Alice"},
    {"id": 2, "name": "Personal Calendar", "owner": "Alice"},
]

placeholder_events = [
    {"id": 1, "calendar_id": 1, "title": "Team Meeting", "date": "2026-04-15", "time": "10:00"},
    {"id": 2, "calendar_id": 2, "title": "Gym Session", "date": "2026-04-16", "time": "18:00"},
]

placeholder_friends = ["Jamie", "Morgan", "Taylor"]
placeholder_externals = ["Google Calendar", "Outlook Calendar"]
placeholder_logs = [
    "[INFO] User Alice synced Google Calendar",
    "[WARN] Failed login attempt detected",
    "[INFO] Admin sent system-wide notification",
]


def _ui_user():
    # get the user dict from the flask session
    usr = session.get("ui_user")
    # check if its a dict
    isDict = isinstance(usr, dict)
    # if its a dict and has an id then its a valid user
    if isDict == True and usr.get("id"):
        return usr
    # otherwise return None meaning no user is logged in
    return None


def _get_ui_supabase_client():
    # get the current user data from session
    userData = _ui_user() or {}
    # get the access token from user data
    tok = userData.get("access_token")
    # if there is no token we cant make authenticated requests
    if not tok:
        raise RuntimeError("No token in session, can't auth calDb")
    # get the supabase client and authenticate it with the token
    calDb = get_supabase_client()
    calDb.postgrest.auth(tok)
    return calDb


def ui_login_required(view_func):
    # this is a decorator that checks if the user is logged in
    # if they are not logged in it redirects them to the login page
    # we use wraps to keep the original function name and docstring
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        # check if there is a user in the session
        if not _ui_user():
            # no user so send them to login
            # we pass the current path so they come back after logging in
            return redirect(url_for("ui.login", next=request.path))
        # user is logged in so call the actual function
        return view_func(*args, **kwargs)
    return wrapped

def _format_login_error(exception):
    # pull the message and code out of the exception
    # supabase exceptions sometimes have a message attribute
    msg = (getattr(exception, "message", None) or str(exception) or "").strip()
    code = (getattr(exception, "code", None) or "").strip()

    norm = msg.lower() #normalize so we can compare easily
    # check if the error is about email not being confirmed
    if "email not confirmed" in norm or code == "email_not_confirmed":
        if code:
            return (
                "Your account is not verified yet. Check your email for the verification link "
                f"and try again. (code: {code})"
            )
        return "Your account is not verified yet. Check your email for the verification link and try again."

    # if there is a code include it in the message
    if code:
        return f"Login failed: {msg} (code: {code})"

    # fallback for any other error
    return "Invalid credentials"


def _resolve_app_base_url():
    # this function figures out what the base url of the app is
    # we need this so we can build full urls for things like oauth redirects
    # first we check if there is an environment variable set for it
    # os.environ.get returns None if the variable doesnt exist
    # we use or "" so we always have a string not None
    baseUrl = (os.environ.get("APP_BASE_URL") or "").strip().rstrip("/")
    # now check if we got a url from the environment
    # if baseUrl is empty that means the env var was not set
    if not baseUrl:
        # fall back to getting the root url from the current request
        # request.url_root is like http://localhost:5000/
        # we use rstrip to remove the trailing slash
        baseUrl = request.url_root.rstrip("/")
    # return whatever url we ended up with
    return baseUrl


def _google_oauth_config():
    # this just reads the google oauth credentials from env vars
    # we need both of these to do the oauth flow
    cId = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    cSecret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    return cId, cSecret



def build_month_preview_data(events_for_calendar):
    # get todays date so we know which month to build
    today = date.today()
    year = today.year
    month = today.month

    # count how many events fall on each day of the month
    # evtCounts is a dict where the key is the day number
    evtCounts = {}
    for event in events_for_calendar:
        raw = str(event.get("start_timestamp") or "")
        try:
            # parse the timestamp into a datetime object
            # we only use the first 19 chars to cut off timezone info
            dt = datetime.fromisoformat(raw[:19])
        except ValueError:
            # if the timestamp is not a valid datetime we just skip this event
            continue
        # check if this event is in the current month
        if dt.year == year and dt.month == month:
            # increment the count for this day
            if dt.day in evtCounts:
                evtCounts[dt.day] = evtCounts[dt.day] + 1
            else:
                evtCounts[dt.day] = 1

    # build the weeks list for the calendar grid
    # each week is a list of day objects with a day number and event count
    weeks = []
    for week in pycalendar.monthcalendar(year, month):
        row = []
        for d in week:
            # pycalendar uses 0 for days outside the month
            if d != 0:
                dayVal = d
            else:
                dayVal = None
            row.append({"day": dayVal, "count": evtCounts.get(d, 0)})
        weeks.append(row)

    return {
        "month_label": f"{pycalendar.month_name[month]} {year}",
        "weeks": weeks,
    }


def guest_nav():
    # this builds the nav list for guests
    # guests are users who are not logged in
    # we return a list where each item has a label and an href
    # label is the text that shows in the nav
    # href is the url it goes to when clicked
    # url_for turns a function name into an actual url
    navList = []
    navList.append({"label": "View Calendars", "href": url_for("ui.view_calendars")})
    navList.append({"label": "View Events", "href": url_for("ui.view_events")})
    # return the nav list
    return navList


def features_nav():
    # check if someone is logged in
    # we show different nav items depending on whether they are logged in or not
    if _ui_user():
        return [
            {"label": "Friends", "href": url_for("ui.manage_friends")},
        ]
    else:
        # not logged in so show links that go to login for protected stuff
        return [
            {"label": "Calendars", "href": url_for("ui.view_calendars")},
            {"label": "Friends", "href": url_for("ui.login", next=url_for("ui.manage_friends"))},
            {"label": "Events", "href": url_for("ui.view_events")},
        ]


def user_nav():
    # build the nav links for logged in users
    # each dict has a label and an href
    return [
        {"label": "Dashboard", "href": url_for("ui.dashboard", role="user")},
        {"label": "Manage Externals", "href": url_for("ui.manage_externals")},
        {"label": "Manage Calendars", "href": url_for("ui.manage_calendars")},
        {"label": "Manage Friends", "href": url_for("ui.manage_friends")},
        {"label": "Remove Account", "href": url_for("ui.remove_account")},
    ]

def admin_nav():
    # same as user_nav but for admins
    # admins have different pages they can go to
    return [
        {"label": "Dashboard", "href": url_for("ui.dashboard", role="admin")},
        {"label": "System Logs", "href": url_for("ui.system_logs")},
        {"label": "Notifications", "href": url_for("ui.send_notification")},
        {"label": "Suspend User", "href": url_for("ui.suspend_user")},
        {"label": "Unlink External Calendars", "href": url_for("ui.admin_unlink")},
    ]


def render_page(title, role, nav, template, **ctx):
    # this just calls render_template with the standard args we always pass
    # title, role, and nav go to every page
    # ctx is any extra stuff the specific page needs
    return render_template(template, title=title, role=role, nav=nav, **ctx)



from api.ui_routes import ui_bp  # noqa: E402: imported here to avoid circular import


@ui_bp.context_processor
def _inject_globals():
    # inject variables that every template can use
    # this runs before every request so the template always has fresh data
    return {
        "ui_user": _ui_user(),
        "features_nav": features_nav(),
        "build_info": BUILD_INFO,
    }
