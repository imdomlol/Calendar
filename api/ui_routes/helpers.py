import calendar as pycalendar
from functools import wraps
import os
from datetime import date
import subprocess
from datetime import datetime

from flask import redirect, render_template, request, session, url_for

from utils.supabase_client import get_supabase_client


def _compute_build_info():
    sha = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "").strip()
    shortSha = sha[:7] if sha else ""
    commitDate = ""

    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%h|||%cd", "--date=format:%b %d %Y, %H:%M"],
            capture_output=True, text=True, timeout=2,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split("|||", 1)
            if not shortSha:
                shortSha = parts[0]
            if len(parts) > 1:
                commitDate = parts[1]
    except Exception:
        pass

    if not shortSha and not commitDate:
        return None
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
    usr = session.get("ui_user")
    isDict = isinstance(usr, dict)
    if isDict == True and usr.get("id"):
        return usr
    return None



def _get_ui_supabase_client():
    userData = _ui_user() or {}
    tok = userData.get("access_token")
    if not tok:
        raise RuntimeError("Login session expired. Please log in again.")
    sb = get_supabase_client()
    sb.postgrest.auth(tok)
    return sb

def ui_login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not _ui_user():
            return redirect(url_for("ui.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


def _format_login_error(exception):
    msg = (getattr(exception, "message", None) or str(exception) or "").strip()
    code = (getattr(exception, "code", None) or "").strip()

    norm = msg.lower() #normalize so we can compare easily
    if "email not confirmed" in norm or code == "email_not_confirmed":
        if code:
            return (
                "Your account is not verified yet. Check your email for the verification link "
                f"and try again. (code: {code})"
            )
        return "Your account is not verified yet. Check your email for the verification link and try again."

    if code:
        return f"Login failed: {msg} (code: {code})"

    return "Invalid credentials."




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
    today = date.today()
    year = today.year
    month = today.month

    evtCounts = {}
    for event in events_for_calendar:
        raw = str(event.get("start_timestamp") or "")
        try:
            dt = datetime.fromisoformat(raw[:19])
        except ValueError:
            continue
        if dt.year == year and dt.month == month:
            if dt.day in evtCounts:
                evtCounts[dt.day] = evtCounts[dt.day] + 1
            else:
                evtCounts[dt.day] = 1

    weeks = []
    for week in pycalendar.monthcalendar(year, month):
        row = []
        for d in week:
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
    if _ui_user():
        return [
            {"label": "Friends", "href": url_for("ui.manage_friends")},
        ]
    else:
        return [
            {"label": "Calendars", "href": url_for("ui.view_calendars")},
            {"label": "Friends", "href": url_for("ui.login", next=url_for("ui.manage_friends"))},
            {"label": "Events", "href": url_for("ui.view_events")},
        ]




def user_nav():
    return [
        {"label": "Dashboard", "href": url_for("ui.dashboard", role="user")},
        {"label": "Manage Externals", "href": url_for("ui.manage_externals")},
        {"label": "Manage Calendars", "href": url_for("ui.manage_calendars")},
        {"label": "Manage Friends", "href": url_for("ui.manage_friends")},
        {"label": "Remove Account", "href": url_for("ui.remove_account")},
    ]

def admin_nav():
    return [
        {"label": "Dashboard", "href": url_for("ui.dashboard", role="admin")},
        {"label": "System Logs", "href": url_for("ui.system_logs")},
        {"label": "Notifications", "href": url_for("ui.send_notification")},
        {"label": "Suspend User", "href": url_for("ui.suspend_user")},
        {"label": "Unlink External Calendars", "href": url_for("ui.admin_unlink")},
    ]


def render_page(title, role, nav, template, **ctx):
    return render_template(template, title=title, role=role, nav=nav, **ctx)



from api.ui_routes import ui_bp  # noqa: E402 — imported here to avoid circular import


@ui_bp.context_processor
def _inject_globals():
    return {
        "ui_user": _ui_user(),
        "features_nav": features_nav(),
        "build_info": BUILD_INFO,
    }
