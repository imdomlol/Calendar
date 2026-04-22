from flask import jsonify, request
from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page, ui_admin_required, admin_nav, placeholder_externals
from utils.logger import _get_logger_client


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
        client = _get_logger_client()

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


@ui_bp.route("/admin/notifications")
@ui_admin_required
def send_notification():
    # show the notifications page
    # admin can send messages from here
    return render_page("Notifications", "admin", admin_nav(), "admin/notification.html")


@ui_bp.route("/admin/suspend")
@ui_admin_required
def suspend_user():
    navData = admin_nav() #admin nav
    # render the suspend user page
    return render_page("Suspend User", "admin", navData, "admin/suspend.html")

@ui_bp.route("/admin/unlink")
@ui_admin_required
def admin_unlink():
    # get providers list for unlink page
    provs = placeholder_externals
    # pass the providers to the template so the admin can pick one to unlink
    return render_page("Unlink External Calendars", "admin", admin_nav(), "admin/unlink.html",
                       providers=provs)
