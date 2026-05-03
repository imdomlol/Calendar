from flask import jsonify, redirect, request, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page, ui_admin_required, _make_ui_user
from models.admin import Admin
from utils.logger import get_logger_client


# ========================= Log Routes =========================

# show the system log page for admins
@ui_bp.route("/admin/logs")
@ui_admin_required
def system_logs():
    # the actual log data is loaded by javascript after the page loads
    return render_page("System Logs", "admin/logs.html")


# return log rows as JSON for the admin logs page
@ui_bp.route("/admin/logs/data")
@ui_admin_required
def system_logs_data():
    # these are the only column names we allow for sorting
    allowedSortColumns = [
        "created_at",
        "level",
        "event_type",
        "message",
        "user_id",
        "path",
        "method",
        "status_code",
    ]

    # get the limit from the query string with 25 as the default
    # we use int() to convert the string to a number
    try:
        limit = int(request.args.get("limit", 25))
    except ValueError:
        # bad input should still give the page some results
        limit = 25

    # clamp limit so nobody asks for 0 or 1000000000000 rows
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    # get the sort column from the query string
    sortColumn = request.args.get("sort", "created_at")

    # make sure the sort column is one we allow
    # if it is not in our list we just fall back to created_at
    if sortColumn not in allowedSortColumns:
        sortColumn = "created_at"

    # get the sort direction with newest first as the default
    sortDirection = request.args.get("dir", "desc")

    # only allow asc or desc and anything else becomes desc
    if sortDirection != "asc" and sortDirection != "desc":
        sortDirection = "desc"
    isDesc = sortDirection == "desc"
    logs = []

    # try to get the logs from supabase
    try:
        client = get_logger_client()

        # if client is None the secret key env var is not set
        if client is not None:
            logsQuery = client.table("logs")
            logsQuery = logsQuery.select(
                "level, event_type, message, user_id, path, method, status_code, details, created_at"
            )
            logsQuery = logsQuery.order(sortColumn, desc=isDesc)
            logsQuery = logsQuery.limit(limit)
            result = logsQuery.execute()
            logs = result.data or []

    except Exception as err:
        print("WARNING: could not fetch logs from supabase - " + str(err))
        return jsonify({"error": "Could not fetch logs", "logs": []}), 500

    return jsonify({"logs": logs})


# ========================= Notification Routes =========================

# show and update the active system wide notification
@ui_bp.route("/admin/notifications", methods=["GET", "POST"])
@ui_admin_required
def send_notification():
    if request.method == "POST":
        # read the admin message from the form
        message = request.form.get("message", "").strip()
        if message:
            Admin.send_system_wide_notifications(message)
        return redirect(url_for("ui.send_notification"))

    # fetch the current banner text for the page
    activeMessage = Admin.get_active_notification_message()

    return render_page(
        "Notifications",
        "admin/notification.html",
        active_message=activeMessage,
    )


# clear the active admin notification
@ui_bp.route("/admin/notifications/clear", methods=["POST"])
@ui_admin_required
def clear_notification():
    Admin.clear_active_notifications()

    # redirect to clear notif from admin view
    return redirect(url_for("ui.send_notification"))


# ========================= User Admin Routes =========================

# search for a user and suspend the selected account
@ui_bp.route("/admin/suspend", methods=["GET", "POST"])
@ui_admin_required
def suspend_user():
    if request.method == "POST":
        # get the selected user id from the form
        userId = request.form.get("user_id", "").strip()
        if userId:
            adminUser = _make_ui_user()
            admin = Admin(userId=adminUser.userId, displayName=adminUser.displayName)
            admin.suspend_user_account(userId)
        return redirect(url_for("ui.suspend_user"))

    # q can be an email display name or id
    queryText = request.args.get("q", "").strip()
    targetUser = Admin.find_user_by_query(queryText)

    return render_page(
        "Suspend User",
        "admin/suspend.html",
        q=queryText,
        target_user=targetUser,
    )


# list all users for admin management
@ui_bp.route("/admin/users")
@ui_admin_required
def admin_users():
    users = Admin.list_all_users()
    return render_page("Manage Users", "admin/users.html", users=users)


# toggle whether a user has admin access
@ui_bp.route("/admin/users/<userId>/toggle-admin", methods=["POST"])
@ui_admin_required
def admin_toggle_admin(userId):
    newValue = Admin.toggle_user_admin(userId)

    if newValue is None:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"is_admin": newValue})


# ========================= External Calendar Routes =========================

# search for a users linked external calendars
@ui_bp.route("/admin/unlink")
@ui_admin_required
def admin_unlink():
    queryText = request.args.get("q", "").strip()
    targetUser = Admin.find_user_by_query(queryText)
    externals = []

    if targetUser:
        externals = Admin.list_externals_for_user(targetUser["id"])

    return render_page(
        "Unlink External Calendars",
        "admin/unlink.html",
        q=queryText,
        target_user=targetUser,
        externals=externals,
    )


# unlink one external calendar by id
@ui_bp.route("/admin/unlink/<externalId>", methods=["POST"])
@ui_admin_required
def admin_unlink_external(externalId):
    wasUnlinked = Admin.unlink_external_by_id(externalId)

    if not wasUnlinked:
        return jsonify({"error": "External not found"}), 404
    
    return jsonify({"ok": True})
