from html import escape

from flask import redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _build_month_preview,
    _get_ui_supabase_client,
    _ui_user,
    guest_nav,
    placeholder_calendars,
    placeholder_events,
    render_page,
    user_nav,
)


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


@ui_bp.route("/calendars")
def view_calendars():
    if not placeholder_calendars:
        body = "<div class='empty'><h3>No calendars found</h3><p>Nothing to display right now.</p></div>"
    else:
        rows = "".join(
            f"<tr><td>{c['id']}</td><td>{c['name']}</td><td>{c['owner']}</td></tr>"
            for c in placeholder_calendars
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
    if not placeholder_events:
        body = "<div class='empty'><h3>No events found</h3><p>Nothing to display right now.</p></div>"
    else:
        rows = "".join(
            f"<tr><td>{e['title']}</td><td>{e['date']}</td><td>{e['time']}</td></tr>"
            for e in placeholder_events
        )
        body = f"""
        <div class='hero'><h1>View Events</h1><p class='muted'>Guest event list.</p></div>
        <table>
          <tr><th>Title</th><th>Date</th><th>Time</th></tr>
          {rows}
        </table>
        """
    return render_page("View Events", "guest", guest_nav(), body)


@ui_bp.route("/dashboard/<role>")
def dashboard(role):
    if role in {"user", "admin"} and not _ui_user():
        return redirect(url_for("ui.login", next=request.path))

    from api.ui_routes.helpers import admin_nav, user_nav

    if role == "admin":
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
        return render_page("Admin Dashboard", "admin", admin_nav(), body)

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
    return render_page("User Dashboard", "user", user_nav(), body)
