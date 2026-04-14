import os
import calendar as pycalendar
from datetime import date
from html import escape
from functools import wraps

from flask import Blueprint, render_template_string, request, redirect, session, url_for
from models.calendar import Calendar
from utils.supabase_client import get_supabase_client

ui_bp = Blueprint("ui", __name__)

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

BASE_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{{ title }}</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #f5f7fb;
      color: #1f2937;
    }
    .topbar {
      background: #1d4ed8;
      color: white;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
    }
    .brand {
      font-size: 22px;
      font-weight: bold;
    }
    .brand a {
      color: inherit;
      text-decoration: none;
    }
    .top-links a {
      color: white;
      text-decoration: none;
      margin-left: 10px;
      font-size: 14px;
      background: rgba(255,255,255,0.15);
      padding: 8px 12px;
      border-radius: 8px;
      display: inline-block;
    }
    .layout {
      display: grid;
      grid-template-columns: 240px 1fr;
      min-height: calc(100vh - 80px);
    }
    .sidebar {
      background: #ffffff;
      border-right: 1px solid #e5e7eb;
      padding: 20px;
    }
    .sidebar h3 {
      margin-top: 0;
      font-size: 18px;
    }
    .sidebar a {
      display: block;
      padding: 10px 12px;
      margin-bottom: 8px;
      text-decoration: none;
      color: #1f2937;
      border-radius: 8px;
    }
    .sidebar a:hover {
      background: #eff6ff;
      color: #1d4ed8;
    }
    .content {
      padding: 24px;
    }
    .hero {
      background: linear-gradient(135deg, #dbeafe, #eff6ff);
      padding: 24px;
      border-radius: 16px;
      margin-bottom: 20px;
      border: 1px solid #bfdbfe;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 18px;
      border: 1px solid #e5e7eb;
      box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    }
    .card h4 {
      margin: 0 0 10px 0;
    }
    .card p, .card li {
      color: #4b5563;
      font-size: 14px;
    }
    .pill {
      display: inline-block;
      font-size: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #dbeafe;
      color: #1d4ed8;
      margin-bottom: 10px;
    }
    .btn {
      display: inline-block;
      margin-top: 10px;
      text-decoration: none;
      background: #1d4ed8;
      color: white;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 14px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid #e5e7eb;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
    }
    th { background: #eff6ff; }
    .danger { background: #dc2626; }
    .warning { background: #f59e0b; }
    .muted { color: #6b7280; }
    .empty {
      padding: 30px;
      text-align: center;
      background: white;
      border: 1px dashed #cbd5e1;
      border-radius: 16px;
    }
    @media (max-width: 860px) {
      .layout { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid #e5e7eb; }
      .content { padding: 18px; }
      .top-links a { margin-left: 6px; margin-top: 6px; }
    }
  </style>
</head>
<body>
  <div class=\"topbar\">
    <div class=\"brand\"><a href=\"{{ url_for('ui.brand_home') }}\">Calendar System</a></div>
    <div class=\"top-links\">
      {% if ui_user %}
      <a href="{{ url_for('ui.logout') }}">Log Out</a>
      {% else %}
      <a href="{{ url_for('ui.login', next=request.path) }}">Log In</a>
      <a href="{{ url_for('ui.register', next=request.path) }}">Register</a>
      {% endif %}
    </div>
  </div>

  <div class=\"layout\">
    <aside class="sidebar">
      {% for item in features_nav %}
        <a href=\"{{ item.href }}\">{{ item.label }}</a>
      {% endfor %}
    </aside>

    <main class=\"content\">
      {{ body|safe }}
    </main>
  </div>
</body>
</html>
"""


def render_page(title, role, nav, body):
    return render_template_string(
        BASE_HTML,
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
    ]
  return [
    {"label": "Calendars", "href": url_for("ui.view_calendars")},
    {"label": "Friends", "href": url_for("ui.login", next=url_for("ui.manage_friends"))},
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
      <div class='card'>
        <h4>Quick actions</h4>
        <p>Create or manage calendars from the Calendars feature page.</p>
        <a class='btn' href='/ui/user/calendars'>Manage Calendars</a>
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

                app_base_url = (os.environ.get("APP_BASE_URL") or "").strip().rstrip("/")
                if not app_base_url:
                  app_base_url = request.url_root.rstrip("/")

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
