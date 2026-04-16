import os
import subprocess
import calendar as pycalendar
from datetime import date
from functools import wraps

from flask import render_template, request, redirect, session, url_for
from utils.supabase_client import get_supabase_client


# ---------------------------------------------------------------------------
# Build info (computed once at startup)
# ---------------------------------------------------------------------------

def _compute_build_info():
    # Vercel injects these env vars at deploy time
    sha = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "").strip()
    short_sha = sha[:7] if sha else ""
    commit_date = ""

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h|||%cd", "--date=format:%b %d %Y, %H:%M"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|||", 1)
            if not short_sha:
                short_sha = parts[0]
            if len(parts) > 1:
                commit_date = parts[1]
    except Exception:
        pass

    if not short_sha and not commit_date:
        return None
    return {"sha": short_sha, "date": commit_date}


BUILD_INFO = _compute_build_info()


# ---------------------------------------------------------------------------
# Placeholder data (demo / not yet persisted)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _ui_user():
    user = session.get("ui_user")
    if isinstance(user, dict) and user.get("id"):
        return user
    return None


def _get_ui_supabase_client():
    user = _ui_user() or {}
    access_token = user.get("access_token")
    if not access_token:
        raise RuntimeError("Login session expired. Please log in again.")
    supabase = get_supabase_client()
    supabase.postgrest.auth(access_token)
    return supabase


def ui_login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not _ui_user():
            return redirect(url_for("ui.login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_login_error(exception):
    message = (getattr(exception, "message", None) or str(exception) or "").strip()
    code = (getattr(exception, "code", None) or "").strip()

    normalized = message.lower()
    if "email not confirmed" in normalized or code == "email_not_confirmed":
        if code:
            return (
                "Your account is not verified yet. Check your email for the verification link "
                f"and try again. (code: {code})"
            )
        return "Your account is not verified yet. Check your email for the verification link and try again."

    if code:
        return f"Login failed: {message} (code: {code})"

    return "Invalid credentials."


def _resolve_app_base_url():
    app_base_url = (os.environ.get("APP_BASE_URL") or "").strip().rstrip("/")
    if not app_base_url:
        app_base_url = request.url_root.rstrip("/")
    return app_base_url


def _google_oauth_config():
    client_id = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    return client_id, client_secret


def build_month_preview_data(events_for_calendar):
    today = date.today()
    year = today.year
    month = today.month

    event_counts = {}
    for event in events_for_calendar:
        start_timestamp = str(event.get("start_timestamp") or "")
        if len(start_timestamp) < 10:
            continue
        date_part = start_timestamp[:10]
        parts = date_part.split("-")
        if len(parts) != 3:
            continue
        try:
            event_year = int(parts[0])
            event_month = int(parts[1])
            event_day = int(parts[2])
        except ValueError:
            continue
        if event_year == year and event_month == month:
            event_counts[event_day] = event_counts.get(event_day, 0) + 1

    weeks = []
    for week in pycalendar.monthcalendar(year, month):
        row = [{"day": d if d != 0 else None, "count": event_counts.get(d, 0)} for d in week]
        weeks.append(row)

    return {
        "month_label": f"{pycalendar.month_name[month]} {year}",
        "weeks": weeks,
    }


# ---------------------------------------------------------------------------
# Navigation builders
# ---------------------------------------------------------------------------

def guest_nav():
    return [
        {"label": "View Calendars", "href": url_for("ui.view_calendars")},
        {"label": "View Events", "href": url_for("ui.view_events")},
    ]


def features_nav():
    if _ui_user():
        return [
            {"label": "Calendars", "href": url_for("ui.manage_calendars")},
            {"label": "Friends", "href": url_for("ui.manage_friends")},
            {"label": "Events", "href": url_for("ui.manage_events")},
        ]
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


# ---------------------------------------------------------------------------
# Page renderer
# ---------------------------------------------------------------------------

def render_page(title, role, nav, template, **ctx):
    return render_template(template, title=title, role=role, nav=nav, **ctx)


# ---------------------------------------------------------------------------
# Blueprint context processor — injects globals into every template
# ---------------------------------------------------------------------------

from api.ui_routes import ui_bp  # noqa: E402 — imported here to avoid circular import


@ui_bp.context_processor
def _inject_globals():
    return {
        "ui_user": _ui_user(),
        "features_nav": features_nav(),
        "build_info": BUILD_INFO,
    }
