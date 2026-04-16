import os
import base64
import hashlib
import calendar as pycalendar
from datetime import date
from html import escape
from functools import wraps

from flask import Blueprint, render_template, request, redirect, session, url_for
from models.calendar import Calendar
from utils.supabase_client import get_supabase_client

ui_bp = Blueprint("ui", __name__, template_folder="templates", static_folder="static")

calendars = [
    {"id": 1, "name": "Work Calendar", "owner": "Alice"},
    {"id": 2, "name": "Personal Calendar", "owner": "Alice"},
]

events = [
    {"id": 1, "calendar_id": 1, "title": "Team Meeting", "date": "2026-04-15", "time": "10:00"},
    {"id": 2, "calendar_id": 2, "title": "Gym Session", "date": "2026-04-16", "time": "18:00"},
]

friends = ["Jamie", "Morgan", "Taylor"]
externals = ["Google Calendar", "Outlook Calendar"]
logs = [
    "[INFO] User Alice synced Google Calendar",
    "[WARN] Failed login attempt detected",
    "[INFO] Admin sent system-wide notification",
]



def render_page(title, role, nav, body):
    return render_template(
        "base.html",
        title=title,
        role=role,
        nav=nav,
        features_nav=features_nav(),
        body=body,
        ui_user=_ui_user(),
    )


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
    client_id = (
        os.environ.get("GOOGLE_CLIENT_ID")
        or ""
    ).strip()
    client_secret = (
        os.environ.get("GOOGLE_CLIENT_SECRET")
        or ""
    ).strip()
    return client_id, client_secret

def _build_month_preview(events_for_calendar):
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

    header = "<tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr>"
    rows = ""
    for week in pycalendar.monthcalendar(year, month):
        cells = ""
        for day in week:
            if day == 0:
                cells += "<td> </td>"
                continue

            count = event_counts.get(day, 0)
            if count:
                cells += (
                    f"<td><strong>{day}</strong><br /><span class='muted' style='font-size:12px;'>{count} event(s)</span></td>"
                )
            else:
                cells += f"<td>{day}</td>"

        rows += f"<tr>{cells}</tr>"

    month_label = f"{pycalendar.month_name[month]} {year}"
    table_html = f"<table>{header}{rows}</table>"
    return month_label, table_html


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


@ui_bp.route("/settings")
def settings_page():
  user = _ui_user()
  role = "user" if user else "guest"
  nav = user_nav() if user else guest_nav()

  status = (request.args.get("status") or "").strip()
  message = (request.args.get("message") or "").strip()

  banner = ""
  if message:
    banner_bg = "#dcfce7" if status == "ok" else "#fee2e2"
    banner_border = "#86efac" if status == "ok" else "#fca5a5"
    banner = (
      f"<div class='card' style='margin-bottom:16px; background:{banner_bg}; border-color:{banner_border};'>"
      f"<p>{escape(message)}</p></div>"
    )

  if not user:
    body = """
    <div class='hero'>
      <h1>Settings</h1>
      <p class='muted'>Sign in to manage external calendar connections.</p>
    </div>
    <div class='card'>
      <h4>External Connections</h4>
      <p>Google API connection controls are available after login.</p>
      <a class='btn' href='/ui/login?next=/ui/settings'>Log In</a>
    </div>
    """
    return render_page("Settings", role, nav, body)

  user_id = user.get("id")
  google_rows = []

  try:
    supabase = _get_ui_supabase_client()
    result = (
      supabase.table("externals")
      .select("id, provider, url")
      .eq("user_id", user_id)
      .execute()
    )
    all_rows = result.data or []
    google_rows = [
      row
      for row in all_rows
      if "google" in str(row.get("provider") or "").lower()
    ]
  except Exception as exc:
    status = "error"
    message = f"Failed to load external connections: {exc}"
    banner = (
      "<div class='card' style='margin-bottom:16px; background:#fee2e2; border-color:#fca5a5;'>"
      f"<p>{escape(message)}</p></div>"
    )

  rows_html = ""
  for row in google_rows:
    external_id = escape(str(row.get("id") or ""))
    provider = escape(str(row.get("provider") or "google"))
    url_value = escape(str(row.get("url") or ""))
    rows_html += f"""
    <tr>
      <td>{provider}</td>
      <td>{url_value}</td>
      <td>{external_id}</td>
      <td>
      <form method='POST' action='/ui/settings/external/google/{external_id}/disconnect' style='margin:0;'>
        <button type='submit' class='btn danger' style='border:none; cursor:pointer; margin-top:0;'>Disconnect</button>
      </form>
      </td>
    </tr>
    """

  if not rows_html:
    rows_html = "<tr><td colspan='4' class='muted'>No Google connections yet.</td></tr>"

  body = """
  <div class='hero'>
    <h1>Settings</h1>
    <p class='muted'>Manage external calendar providers connected to your account.</p>
  </div>
  """ + banner + """
  <div class='grid'>
    <div class='card'>
    <div class='pill'>External Connections</div>
    <h4>Google API</h4>
    <p class='muted'>Sign in with Google to connect your account. No manual token entry required.</p>
    <a class='btn' href='/ui/settings/external/google/login'>Log in with Google</a>
    </div>
    <div class='card'>
    <h4>Connected Google Accounts</h4>
    <table>
      <tr><th>Provider</th><th>URL</th><th>Connection ID</th><th>Action</th></tr>
      """ + rows_html + """
    </table>
    </div>
  </div>
  """
  return render_page("Settings", role, nav, body)


@ui_bp.route("/settings/external/google/connect", methods=["GET", "POST"])
@ui_login_required
def settings_connect_google():
  return redirect(url_for("ui.settings_login_google"))


@ui_bp.route("/settings/external/google/login")
@ui_login_required
def settings_login_google():
  client_id, client_secret = _google_oauth_config()

  if not client_id or not client_secret:
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message=(
        "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
        "GOOGLE_CLIENT_SECRET in your environment."
      ),
    ))

  try:
    from google_auth_oauthlib.flow import Flow
  except Exception as exc:
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message=f"Google OAuth dependency error: {exc}",
    ))

  app_base_url = _resolve_app_base_url()

  redirect_uri = f"{app_base_url}{url_for('ui.settings_google_callback')}"

  flow = Flow.from_client_config(
    {
      "web": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
      }
    },
    scopes=[
      "https://www.googleapis.com/auth/calendar.readonly",
    ],
  )
  flow.redirect_uri = redirect_uri

  code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
  authorization_url, state = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent",
    code_verifier=code_verifier,
  )
  session["google_oauth_state"] = state
  session["google_oauth_code_verifier"] = code_verifier
  session["google_oauth_redirect_uri"] = redirect_uri

  return redirect(authorization_url)


@ui_bp.route("/settings/external/google/callback")
@ui_login_required
def settings_google_callback():
  expected_state = (session.get("google_oauth_state") or "").strip()
  returned_state = (request.args.get("state") or "").strip()

  if not expected_state or returned_state != expected_state:
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)
    session.pop("google_oauth_code_verifier", None)
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message="Google OAuth state check failed. Please try again.",
    ))

  client_id, client_secret = _google_oauth_config()
  redirect_uri = (session.get("google_oauth_redirect_uri") or "").strip()
  code_verifier = (session.get("google_oauth_code_verifier") or "").strip()

  try:
    from google_auth_oauthlib.flow import Flow
  except Exception as exc:
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)
    session.pop("google_oauth_code_verifier", None)
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message=f"Google OAuth dependency error: {exc}",
    ))

  if not client_id or not client_secret or not redirect_uri:
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)
    session.pop("google_oauth_code_verifier", None)
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message="Google OAuth session expired. Please start again.",
    ))

  try:
    flow = Flow.from_client_config(
      {
        "web": {
          "client_id": client_id,
          "client_secret": client_secret,
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
        }
      },
      scopes=[
        "https://www.googleapis.com/auth/calendar.readonly",
      ],
      state=expected_state,
    )
    flow.redirect_uri = redirect_uri
    flow.fetch_token(authorization_response=request.url, code_verifier=code_verifier)
    credentials = flow.credentials

    user_id = _ui_user()["id"]
    provider_url = "https://www.googleapis.com/calendar/v3"
    supabase = _get_ui_supabase_client()

    existing = (
      supabase.table("externals")
      .select("id")
      .eq("user_id", user_id)
      .eq("provider", "google")
      .eq("url", provider_url)
      .execute()
    )

    if existing.data:
      update_payload = {}
      if credentials.token:
        update_payload["access_token"] = credentials.token
      if credentials.refresh_token:
        update_payload["refresh_token"] = credentials.refresh_token
      if update_payload:
        (
          supabase.table("externals")
          .update(update_payload)
          .eq("id", existing.data[0].get("id"))
          .eq("user_id", user_id)
          .execute()
        )
      message = "Google connection refreshed."
    else:
      payload = {
        "user_id": user_id,
        "provider": "google",
        "url": provider_url,
      }
      if credentials.token:
        payload["access_token"] = credentials.token
      if credentials.refresh_token:
        payload["refresh_token"] = credentials.refresh_token

      result = supabase.table("externals").insert(payload).execute()
      created = (result.data or [{}])[0]
      created_id = created.get("id") or "new row"
      message = f"Google connection created (id: {created_id})."

    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)
    session.pop("google_oauth_code_verifier", None)
    return redirect(url_for(
      "ui.settings_page",
      status="ok",
      message=message,
    ))
  except Exception as exc:
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)
    session.pop("google_oauth_code_verifier", None)
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message=f"Failed Google OAuth connection: {exc}",
    ))


@ui_bp.route("/settings/external/google/<external_id>/disconnect", methods=["POST"])
@ui_login_required
def settings_disconnect_google(external_id):
  user_id = _ui_user()["id"]

  try:
    supabase = _get_ui_supabase_client()
    existing = (
      supabase.table("externals")
      .select("id, provider")
      .eq("id", external_id)
      .eq("user_id", user_id)
      .execute()
    )

    rows = existing.data or []
    if not rows:
      return redirect(url_for(
        "ui.settings_page",
        status="error",
        message="Connection not found.",
      ))

    provider_value = str(rows[0].get("provider") or "").lower()
    if "google" not in provider_value:
      return redirect(url_for(
        "ui.settings_page",
        status="error",
        message="Only Google connections can be removed from this section.",
      ))

    supabase.table("externals").delete().eq("id", external_id).eq("user_id", user_id).execute()
    return redirect(url_for(
      "ui.settings_page",
      status="ok",
      message="Google connection disconnected.",
    ))
  except Exception as exc:
    return redirect(url_for(
      "ui.settings_page",
      status="error",
      message=f"Failed to disconnect Google connection: {exc}",
    ))


@ui_bp.route("/")
def home():
    user = _ui_user()

    if not user:
        body = """
        <div class='hero'>
          <h1>Welcome to the Calendar System</h1>
          <p class='muted'>Guest preview with an empty calendar. Log in to view your real calendars.</p>
        </div>

        <div class='card'>
          <h4>Calendar Preview</h4>
          <table>
            <tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr>
            <tr><td> </td><td> </td><td> </td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
            <tr><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td></tr>
            <tr><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td></tr>
            <tr><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td><td>24</td><td>25</td></tr>
            <tr><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td> </td><td> </td></tr>
          </table>
          <p class='muted' style='margin-top:12px;'>No events to show for guests.</p>
        </div>
        """
        return render_page("Calendar Info System", "guest", guest_nav(), body)

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

    status_block = ""
    if status_message:
        status_block = (
            "<div class='card' style='margin-bottom:16px; background:#fee2e2; border-color:#fca5a5;'>"
            f"<p>{escape(status_message)}</p></div>"
        )

    if not calendars:
        body = """
        <div class='hero'>
          <h1>Welcome back</h1>
          <p class='muted'>You do not have any calendars yet.</p>
        </div>
        """ + status_block + """
        <div class='card'>
          <h4>No calendars found</h4>
          <p>Create your first calendar to start viewing it here.</p>
          <a class='btn' href='/ui/user/calendars'>Go to Calendars</a>
        </div>
        """
        return render_page("Calendar Home", "user", user_nav(), body)

    option_tags = "".join(
        (
            f"<option value='{escape(str(c.get('id')))}'"
            + (" selected" if str(c.get("id")) == selected_calendar_id else "")
            + f">{escape(str(c.get('name') or 'Untitled Calendar'))}</option>"
        )
        for c in calendars
    )

    calendar_name = escape(str(selected_calendar.get("name") or "Untitled Calendar"))
    month_label, month_table = _build_month_preview(events_for_calendar)

    body = """
    <div class='hero'>
      <h1>Your Calendar</h1>
      <p class='muted'>Select a calendar to preview it on your home page.</p>
    </div>
    """ + status_block + """
    <div class='card' style='margin-bottom:16px;'>
      <form method='GET' action='/ui/' style='display:flex; gap:8px; align-items:center; flex-wrap:wrap;'>
        <label for='calendar_id'><strong>Calendar:</strong></label>
        <select id='calendar_id' name='calendar_id' style='padding:8px; border:1px solid #cbd5e1; border-radius:8px; min-width:240px;'>
          """ + option_tags + """
        </select>
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0;'>Switch</button>
      </form>
    </div>
    <div class='grid'>
      <div class='card'>
        <div class='pill'>Preview</div>
        <h4>""" + calendar_name + """</h4>
        <p class='muted'>""" + escape(month_label) + """</p>
        """ + month_table + """
      </div>
    </div>
    """
    return render_page("Calendar Home", "user", user_nav(), body)


@ui_bp.route("/home")
def brand_home():
    return redirect(url_for("ui.home"))


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    info = (request.args.get("info") or "").strip()
    next_path = (request.args.get("next") or "").strip() or url_for("ui.dashboard", role="user")
    if not next_path.startswith("/"):
        next_path = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            error = "Email and password are required."
        else:
            try:
                supabase = get_supabase_client()
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                user_obj = getattr(result, "user", None)
                session_obj = getattr(result, "session", None)
                user_id = getattr(user_obj, "id", None)
                access_token = getattr(session_obj, "access_token", None)
                if not user_id:
                    error = "Login failed."
                else:
                    session["ui_user"] = {
                        "id": user_id,
                        "email": getattr(user_obj, "email", email),
                    "access_token": access_token,
                    }
                    return redirect(next_path)
            except Exception as exc:
                error = _format_login_error(exc)

    error_block = ""
    if error:
        error_block = f"<p style='color:#b91c1c; margin:0 0 12px 0;'>{escape(error)}</p>"

    info_block = ""
    if info and not error:
        info_block = f"<p style='color:#166534; margin:0 0 12px 0;'>{escape(info)}</p>"

    body = f"""
    <div class='hero'>
      <h1>Log In</h1>
      <p class='muted'>Sign in to access user and admin pages.</p>
    </div>
    <div class='card'>
      {info_block}
      {error_block}
      <form method='POST' action='/ui/login?next={escape(next_path)}' style='display:flex; flex-direction:column; gap:10px; max-width:420px;'>
      <input type='email' name='email' placeholder='Email' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='password' placeholder='Password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <button type='submit' class='btn' style='border:none; cursor:pointer; width:max-content; margin-top:0;'>Log In</button>
      </form>
      <p class='muted' style='margin-top:12px;'>Need an account? <a href='/ui/register?next={escape(next_path)}'>Register here</a></p>
    </div>
    """
    return render_page("Log In", "guest", guest_nav(), body)


@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    next_path = (request.args.get("next") or "").strip() or url_for("ui.dashboard", role="user")
    if not next_path.startswith("/"):
        next_path = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not email or not password:
            error = "Email and password are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            try:
                supabase = get_supabase_client()
                payload = {
                    "email": email,
                    "password": password,
                }

                app_base_url = _resolve_app_base_url()

                options = {
                  "email_redirect_to": f"{app_base_url}{url_for('ui.login')}",
                }
                if name:
                  options["data"] = {"name": name}

                payload["options"] = options

                supabase.auth.sign_up(payload)

                return redirect(url_for(
                    "ui.login",
                    next=next_path,
                  info=(
                    "Account created. Please check your email to verify your account "
                    "before logging in."
                  ),
                ))
            except Exception as exc:
                error = f"Could not register: {exc}"

    error_block = ""
    if error:
        error_block = f"<p style='color:#b91c1c; margin:0 0 12px 0;'>{escape(error)}</p>"

    body = f"""
    <div class='hero'>
      <h1>Register</h1>
      <p class='muted'>Create an account to access calendar management.</p>
    </div>
    <div class='card'>
      {error_block}
      <form method='POST' action='/ui/register?next={escape(next_path)}' style='display:flex; flex-direction:column; gap:10px; max-width:420px;'>
      <input type='text' name='name' placeholder='Name (optional)' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='email' name='email' placeholder='Email' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='password' placeholder='Password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='confirm_password' placeholder='Confirm password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <button type='submit' class='btn' style='border:none; cursor:pointer; width:max-content; margin-top:0;'>Create Account</button>
      </form>
      <p class='muted' style='margin-top:12px;'>Already have an account? <a href='/ui/login?next={escape(next_path)}'>Log in</a></p>
    </div>
    """
    return render_page("Register", "guest", guest_nav(), body)


@ui_bp.route("/logout")
def logout():
    session.pop("ui_user", None)
    return redirect(url_for("ui.home"))


@ui_bp.route("/dashboard/<role>")
def dashboard(role):
    if role in {"user", "admin"} and not _ui_user():
        return redirect(url_for("ui.login", next=request.path))

    if role == "admin":
        nav = admin_nav()
        body = """
        <div class='hero'>
          <h1>Admin Dashboard</h1>
          <p class='muted'>Manage system-wide actions from one place.</p>
        </div>
        <div class='grid'>
          <div class='card'><h4>View system logs</h4><p>Inspect recent platform activity.</p><a class='btn' href='/ui/admin/logs'>Open</a></div>
          <div class='card'><h4>Send notifications</h4><p>Push platform updates to all users.</p><a class='btn warning' href='/ui/admin/notifications'>Open</a></div>
          <div class='card'><h4>Suspend user account</h4><p>Temporarily disable access.</p><a class='btn danger' href='/ui/admin/suspend'>Open</a></div>
          <div class='card'><h4>Unlink all external calendars</h4><p>Break linked external integrations.</p><a class='btn' href='/ui/admin/unlink'>Open</a></div>
        </div>
        """
        return render_page("Admin Dashboard", "admin", nav, body)

    nav = user_nav()
    body = """
    <div class='hero'>
      <h1>User Dashboard</h1>
      <p class='muted'>Manage your calendars, friends, external calendars, and events.</p>
    </div>
    <div class='grid'>
      <div class='card'><h4>Manage Externals</h4><p>Connect, disconnect, or sync Google/Outlook calendars.</p><a class='btn' href='/ui/user/externals'>Open</a></div>
      <div class='card'><h4>Manage Calendars</h4><p>Create calendars and manage events.</p><a class='btn' href='/ui/user/calendars'>Open</a></div>
      <div class='card'><h4>Manage Friends</h4><p>Add and remove friends from your list.</p><a class='btn' href='/ui/user/friends'>Open</a></div>
      <div class='card'><h4>Remove Account</h4><p>Delete your user account.</p><a class='btn danger' href='/ui/user/remove-account'>Open</a></div>
    </div>
    """
    return render_page("User Dashboard", "user", nav, body)


@ui_bp.route("/calendars")
def view_calendars():
    if not calendars:
        body = "<div class='empty'><h3>No calendars found</h3><p>Nothing to display right now.</p></div>"
    else:
        rows = "".join(
            f"<tr><td>{c['id']}</td><td>{c['name']}</td><td>{c['owner']}</td></tr>" for c in calendars
        )
        body = f"""
        <div class='hero'><h1>View Calendars</h1><p class='muted'>Guest access to available calendars.</p></div>
        <table>
          <tr><th>ID</th><th>Calendar Name</th><th>Owner</th></tr>
          {rows}
        </table>
        """
    return render_page("View Calendars", "guest", guest_nav(), body)


@ui_bp.route("/events")
def view_events():
    if not events:
        body = "<div class='empty'><h3>No events found</h3><p>Nothing to display right now.</p></div>"
    else:
        rows = "".join(
            f"<tr><td>{e['title']}</td><td>{e['date']}</td><td>{e['time']}</td></tr>" for e in events
        )
        body = f"""
        <div class='hero'><h1>View Events</h1><p class='muted'>Guest event list.</p></div>
        <table>
          <tr><th>Title</th><th>Date</th><th>Time</th></tr>
          {rows}
        </table>
        """
    return render_page("View Events", "guest", guest_nav(), body)


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    items = "".join(f"<li>{name}</li>" for name in externals)
    body = f"""
    <div class='hero'><h1>Manage Externals</h1><p class='muted'>Connect, disconnect, sync now, or toggle auto-sync.</p></div>
    <div class='grid'>
      <div class='card'><h4>Connected providers</h4><ul>{items}</ul></div>
      <div class='card'><h4>Actions</h4><p>Connect external calendar</p><p>Disconnect external calendar</p><p>Sync now</p><p>Enable/Disable auto sync</p></div>
    </div>
    """
    return render_page("Manage Externals", "user", user_nav(), body)


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    owner_id = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    records = []
    if owner_id:
      try:
        supabase = _get_ui_supabase_client()
        result = (
          supabase.table("calendars")
          .select("id, name, owner_id, member_ids, events")
          .eq("owner_id", owner_id)
          .order("age_timestamp", desc=False)
          .execute()
        )
        records = result.data or []
      except Exception as exc:
        status = "error"
        message = f"Failed to load calendars: {exc}"

    cards = []
    for cal in records:
        calendar_id = escape(str(cal.get("id") or ""))
        calendar_name = escape(str(cal.get("name") or "Untitled"))
        calendar_owner = escape(str(cal.get("owner_id") or ""))
        member_list = cal.get("member_ids") or []
        members = "".join(f"<li>{escape(str(member))}</li>" for member in member_list) or "<li>No members yet</li>"
        event_count = len(cal.get("events") or [])
        cards.append(f"""
          <div class='card'>
            <div class='pill'>Calendar #{calendar_id}</div>
            <h4>{calendar_name}</h4>
            <p>Owner ID: {calendar_owner}</p>
            <p>Events linked: {event_count}</p>
            <p><strong>Actions:</strong> Create event, edit event, delete event, manage members, remove calendar</p>
            <ul>{members}</ul>
          </div>
        """)

    banner = ""
    if message:
        banner_class = "#dcfce7" if status == "ok" else "#fee2e2"
        border_class = "#86efac" if status == "ok" else "#fca5a5"
        banner = f"<div class='card' style='margin-bottom:16px; background:{banner_class}; border-color:{border_class};'><p>{escape(message)}</p></div>"

    if not cards:
        results_section = "<div class='empty'><h3>No calendars found</h3><p>No calendar rows exist for this owner id yet.</p></div>"
    else:
        results_section = "<div class='grid'>" + "".join(cards) + "</div>"

    safe_owner_value = escape(owner_id)
    body = """
    <div class='hero'>
      <h1>Manage Calendars</h1>
      <p class='muted'>Create calendars in Supabase. Owner id is auto-filled from your login.</p>
    </div>
    """ + banner + """
    <div class='card' style='margin-bottom:16px;'>
      <h4>Available actions</h4>
      <p>Create Calendar • Add Member • Remove Member • Manage Events • Remove Calendar</p>
      <p class='muted'>Logged in as owner id: """ + safe_owner_value + """</p>
      <form method='POST' action='/ui/user/calendars/create' style='margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;'>
        <input type='hidden' name='owner_id' value='""" + safe_owner_value + """' />
        <input
          type='text'
          name='name'
          placeholder='Calendar name (required)'
          required
          style='padding:10px; border:1px solid #cbd5e1; border-radius:10px; min-width:220px;'
        />
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0;'>Create Calendar</button>
      </form>
    </div>
    """ + results_section
    return render_page("Manage Calendars", "user", user_nav(), body)


@ui_bp.route("/user/calendars/create", methods=["POST"])
@ui_login_required
def create_calendar():
    name = (request.form.get("name") or "").strip()
    owner_id = _ui_user()["id"]

    if not owner_id or not name:
        return redirect(url_for(
            "ui.manage_calendars",
            owner_id=owner_id,
            status="error",
            message="Owner ID and calendar name are required.",
        ))

    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("calendars")
            .insert({
                "name": name,
                "owner_id": owner_id,
                "member_ids": [owner_id],
                "events": [],
            })
            .execute()
        )
        created = (result.data or [{}])[0]
        created_id = created.get("id") or "new row"
        return redirect(url_for(
            "ui.manage_calendars",
            owner_id=owner_id,
            status="ok",
            message=f"Calendar created successfully (id: {created_id}).",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.manage_calendars",
            owner_id=owner_id,
            status="error",
            message=f"Failed to create calendar: {exc}",
        ))

@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    user_id = _ui_user()["id"]
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    calendars = []
    events_rows = []

    try:
        supabase = _get_ui_supabase_client()
        calendars_result = (
            supabase.table("calendars")
            .select("id, name")
            .eq("owner_id", user_id)
            .order("age_timestamp", desc=False)
            .execute()
        )
        calendars = calendars_result.data or []

        if calendars:
            if not selected_calendar_id or not any(str(c.get("id")) == selected_calendar_id for c in calendars):
                selected_calendar_id = str(calendars[0].get("id"))

            events_result = (
                supabase.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events_rows = events_result.data or []
    except Exception as exc:
        status = "error"
        message = f"Failed to load events: {exc}"

    banner = ""
    if message:
        banner_bg = "#dcfce7" if status == "ok" else "#fee2e2"
        banner_border = "#86efac" if status == "ok" else "#fca5a5"
        banner = (
            f"<div class='card' style='margin-bottom:16px; background:{banner_bg}; border-color:{banner_border};'>"
            f"<p>{escape(message)}</p></div>"
        )

    if not calendars:
        body = """
        <div class='hero'>
          <h1>Manage Events</h1>
          <p class='muted'>Create events by attaching them to one of your calendars.</p>
        </div>
        """ + banner + """
        <div class='card'>
          <h4>No calendars available</h4>
          <p>Create a calendar first, then come back to add events.</p>
          <a class='btn' href='/ui/user/calendars'>Go to Calendars</a>
        </div>
        """
        return render_page("Manage Events", "user", user_nav(), body)

    calendar_options = "".join(
        (
            f"<option value='{escape(str(c.get('id')))}'"
            + (" selected" if str(c.get("id")) == selected_calendar_id else "")
            + f">{escape(str(c.get('name') or 'Untitled Calendar'))}</option>"
        )
        for c in calendars
    )

    event_rows_html = "".join(
        "<tr>"
        f"<td>{escape(str(event.get('title') or 'Untitled'))}</td>"
        f"<td>{escape(str(event.get('start_timestamp') or ''))}</td>"
        f"<td>{escape(str(event.get('end_timestamp') or ''))}</td>"
        "</tr>"
        for event in events_rows
    )
    if not event_rows_html:
        event_rows_html = "<tr><td colspan='3' class='muted'>No events found for this calendar.</td></tr>"

    body = """
    <div class='hero'>
      <h1>Manage Events</h1>
      <p class='muted'>Create an event and attach it to one of your calendars.</p>
    </div>
    """ + banner + """
    <div class='card' style='margin-bottom:16px;'>
      <form method='GET' action='/ui/user/events' style='display:flex; gap:8px; align-items:center; flex-wrap:wrap;'>
        <label for='calendar_id'><strong>View calendar:</strong></label>
        <select id='calendar_id' name='calendar_id' style='padding:8px; border:1px solid #cbd5e1; border-radius:8px; min-width:240px;'>
          """ + calendar_options + """
        </select>
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0;'>Load</button>
      </form>
    </div>

    <div class='card' style='margin-bottom:16px;'>
      <h4>Add Event</h4>
      <form method='POST' action='/ui/user/events/create' style='display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px;'>
        <select name='calendar_id' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;'>
          """ + calendar_options + """
        </select>
        <input type='text' name='title' placeholder='Event title' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='datetime-local' name='start_timestamp' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='datetime-local' name='end_timestamp' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='text' name='description' placeholder='Description (optional)' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px; grid-column:1/-1;' />
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0; width:max-content;'>Create Event</button>
      </form>
    </div>

    <div class='card'>
      <h4>Events in selected calendar</h4>
      <table>
        <tr><th>Title</th><th>Start</th><th>End</th></tr>
        """ + event_rows_html + """
      </table>
    </div>
    """
    return render_page("Manage Events", "user", user_nav(), body)


@ui_bp.route("/user/events/create", methods=["POST"])
@ui_login_required
def create_event_ui():
    user_id = _ui_user()["id"]
    calendar_id = (request.form.get("calendar_id") or "").strip()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    if not calendar_id or not title:
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="error",
            message="Calendar and title are required.",
        ))

    try:
        supabase = _get_ui_supabase_client()
        ownership = (
            supabase.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", user_id)
            .execute()
        )
        if not ownership.data:
            return redirect(url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="error",
                message="You do not have access to that calendar.",
            ))

        payload = {
            "title": title,
            "owner_id": user_id,
            "calendar_ids": [calendar_id],
        }
        if description:
            payload["description"] = description
        if start_timestamp:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp:
            payload["end_timestamp"] = end_timestamp

        result = supabase.table("events").insert(payload).execute()
        created = (result.data or [{}])[0]
        created_id = created.get("id") or "new row"
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="ok",
            message=f"Event created successfully (id: {created_id}).",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="error",
            message=f"Failed to create event: {exc}",
        ))


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    names = "".join(f"<li>{friend}</li>" for friend in friends)
    body = f"""
    <div class='hero'><h1>Manage Friends</h1><p class='muted'>Add and remove friends.</p></div>
    <div class='grid'>
      <div class='card'><h4>Friends List</h4><ul>{names}</ul></div>
      <div class='card'><h4>Actions</h4><p>Add Friend</p><p>Remove Friend</p></div>
    </div>
    """
    return render_page("Manage Friends", "user", user_nav(), body)


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    body = """
    <div class='hero'><h1>Remove Account</h1><p class='muted'>This is a placeholder confirmation screen.</p></div>
    <div class='card'>
      <h4>Danger Zone</h4>
      <p>This action would permanently remove the user's account.</p>
      <a class='btn danger' href='/ui/dashboard/user'>Confirm removal</a>
    </div>
    """
    return render_page("Remove Account", "user", user_nav(), body)


@ui_bp.route("/admin/logs")
@ui_login_required
def system_logs():
    lines = "".join(f"<tr><td>{i + 1}</td><td>{line}</td></tr>" for i, line in enumerate(logs))
    body = f"""
    <div class='hero'><h1>System Logs</h1><p class='muted'>Admin-only activity log view.</p></div>
    <table>
      <tr><th>#</th><th>Log Entry</th></tr>
      {lines}
    </table>
    """
    return render_page("System Logs", "admin", admin_nav(), body)


@ui_bp.route("/admin/notifications")
@ui_login_required
def send_notification():
    body = """
    <div class='hero'><h1>System-Wide Notifications</h1><p class='muted'>Draft and send a notification to every user.</p></div>
    <div class='card'>
      <h4>Notification Composer</h4>
      <p>Title: Platform Maintenance</p>
      <p>Message: The system will be unavailable tonight from 11PM to 12AM.</p>
      <a class='btn warning' href='/ui/dashboard/admin'>Send Notification</a>
    </div>
    """
    return render_page("Notifications", "admin", admin_nav(), body)


@ui_bp.route("/admin/suspend")
@ui_login_required
def suspend_user():
    body = """
    <div class='hero'><h1>Suspend User Account</h1><p class='muted'>Admin control panel for account suspension.</p></div>
    <div class='card'>
      <h4>Suspend user</h4>
      <p>User: alice@example.com</p>
      <p>Reason: Policy violation / temporary review</p>
      <a class='btn danger' href='/ui/dashboard/admin'>Suspend Account</a>
    </div>
    """
    return render_page("Suspend User", "admin", admin_nav(), body)


@ui_bp.route("/admin/unlink")
@ui_login_required
def admin_unlink():
    providers = "".join(f"<li>{name}</li>" for name in externals)
    body = f"""
    <div class='hero'><h1>Unlink External Calendars</h1><p class='muted'>Admin action for external calendar disconnection.</p></div>
    <div class='card'>
      <h4>Linked providers</h4>
      <ul>{providers}</ul>
      <a class='btn danger' href='/ui/dashboard/admin'>Unlink All</a>
    </div>
    """
    return render_page("Unlink External Calendars", "admin", admin_nav(), body)
