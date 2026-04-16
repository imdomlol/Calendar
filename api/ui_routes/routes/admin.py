from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    admin_nav,
    placeholder_externals,
    placeholder_logs,
    render_page,
    ui_login_required,
)


@ui_bp.route("/admin/logs")
@ui_login_required
def system_logs():
    lines = "".join(f"<tr><td>{i + 1}</td><td>{line}</td></tr>" for i, line in enumerate(placeholder_logs))
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
    providers = "".join(f"<li>{name}</li>" for name in placeholder_externals)
    body = f"""
    <div class='hero'><h1>Unlink External Calendars</h1><p class='muted'>Admin action for external calendar disconnection.</p></div>
    <div class='card'>
      <h4>Linked providers</h4>
      <ul>{providers}</ul>
      <a class='btn danger' href='/ui/dashboard/admin'>Unlink All</a>
    </div>
    """
    return render_page("Unlink External Calendars", "admin", admin_nav(), body)
