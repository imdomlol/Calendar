# admin routes for system management pages (logs, notifications, user suspend, external unlink)
# TODO: all routes are stubs backed by placeholder data and need real database queries
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
    return render_page("System Logs", "admin", admin_nav(), "admin/logs.html",
                       logs=placeholder_logs)


@ui_bp.route("/admin/notifications")
@ui_login_required
def send_notification():
    return render_page("Notifications", "admin", admin_nav(), "admin/notification.html")


@ui_bp.route("/admin/suspend")
@ui_login_required
def suspend_user():
    return render_page("Suspend User", "admin", admin_nav(), "admin/suspend.html")


@ui_bp.route("/admin/unlink")
@ui_login_required
def admin_unlink():
    return render_page("Unlink External Calendars", "admin", admin_nav(), "admin/unlink.html",
                       providers=placeholder_externals)
