from flask import jsonify, redirect, request, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page, ui_admin_required, admin_nav, _make_ui_user
from models.admin import Admin
from utils.logger import get_logger_client


# this is the route that shows system logs for admins
@ui_bp.route("/admin/logs")
@ui_admin_required
def system_logs():
    # get the admin nav links and render the page
    # the actual log data is loaded by javascript after the page loads
    nav = admin_nav()
    return render_page("System Logs", "admin", nav, "admin/logs.html")


# this is the route that javascript calls to get log data as json
# it accepts limit, sort, and dir as query parameters
@ui_bp.route("/admin/logs/data")
@ui_admin_required
def system_logs_data():
    # these are the only column names we allow for sorting
    # we check against this list so nobody can inject a bad column name
    allowed_sort_columns = [
        "created_at",
        "level",
        "event_type",
        "message",
        "user_id",
        "path",
        "method",
        "status_code",
    ]

    # get the limit from the query string, default to 25
    # we use int() to convert the string to a number
    # if the value is not a valid number we fall back to 25
    try:
        limit = int(request.args.get("limit", 25))
    except ValueError:
        limit = 25

    # clamp limit so nobody asks for 0 or a million rows
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    # get the sort column from the query string, default to created_at
    sort_col = request.args.get("sort", "created_at")

    # make sure the sort column is one we allow
    # if its not in our list we just fall back to created_at
    if sort_col not in allowed_sort_columns:
        sort_col = "created_at"

    # get the sort direction, default to descending (newest first)
    sort_dir = request.args.get("dir", "desc")

    # only allow asc or desc, anything else becomes desc
    if sort_dir != "asc" and sort_dir != "desc":
        sort_dir = "desc"

    # figure out if we want descending order
    is_desc = sort_dir == "desc"

    # start with an empty list in case something goes wrong
    logs = []

    # try to get the logs from supabase
    try:
        client = get_logger_client()

        # if client is None it means the secret key env var isnt set
        if client is not None:
            result = (
                client.table("logs")
                .select("level, event_type, message, user_id, path, method, status_code, details, created_at")
                .order(sort_col, desc=is_desc)
                .limit(limit)
                .execute()
            )
            logs = result.data or []

    except Exception as err:
        # something went wrong, return an error response
        print("WARNING: could not fetch logs from supabase - " + str(err))
        return jsonify({"error": "Could not fetch logs", "logs": []}), 500

    # return the logs as json
    return jsonify({"logs": logs})


@ui_bp.route("/admin/notifications", methods=["GET", "POST"])
@ui_admin_required
def send_notification():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            Admin.sendSystemWideNotifications(message)
        return redirect(url_for("ui.send_notification"))

    active_message = Admin.getActiveNotificationMessage()

    return render_page(
        "Notifications",
        "admin",
        admin_nav(),
        "admin/notification.html",
        active_message=active_message,
    )


@ui_bp.route("/admin/notifications/clear", methods=["POST"])
@ui_admin_required
def clear_notification():
    Admin.clearActiveNotifications()
    return redirect(url_for("ui.send_notification"))


@ui_bp.route("/admin/suspend", methods=["GET", "POST"])
@ui_admin_required
def suspend_user():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        if user_id:
            admin_user = _make_ui_user()
            admin = Admin(userId=admin_user.userId, displayName=admin_user.displayName)
            admin.suspendUserAccount(user_id)
        return redirect(url_for("ui.suspend_user"))

    q = request.args.get("q", "").strip()
    target_user = Admin.findUserByQuery(q)
    return render_page(
        "Suspend User",
        "admin",
        admin_nav(),
        "admin/suspend.html",
        q=q,
        target_user=target_user,
    )

@ui_bp.route("/admin/users")
@ui_admin_required
def admin_users():
    users = Admin.listAllUsers()
    return render_page("Manage Users", "admin", admin_nav(), "admin/users.html", users=users)


@ui_bp.route("/admin/users/<user_id>/toggle-admin", methods=["POST"])
@ui_admin_required
def admin_toggle_admin(user_id):
    new_val = Admin.toggleUserAdmin(user_id)
    if new_val is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"is_admin": new_val})


@ui_bp.route("/admin/unlink")
@ui_admin_required
def admin_unlink():
    q = request.args.get("q", "").strip()
    target_user = Admin.findUserByQuery(q)
    externals = []

    if target_user:
        externals = Admin.listExternalsForUser(target_user["id"])

    return render_page(
        "Unlink External Calendars",
        "admin",
        admin_nav(),
        "admin/unlink.html",
        q=q,
        target_user=target_user,
        externals=externals,
    )


@ui_bp.route("/admin/unlink/<external_id>", methods=["POST"])
@ui_admin_required
def admin_unlink_external(external_id):
    ok = Admin.unlinkExternalById(external_id)
    if not ok:
        return jsonify({"error": "External not found"}), 404
    return jsonify({"ok": True})
