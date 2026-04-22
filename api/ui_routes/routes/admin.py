from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page, ui_admin_required, admin_nav, placeholder_externals
from utils.logger import _get_logger_client


# this is the route that shows system logs for admins
@ui_bp.route("/admin/logs")
@ui_admin_required
def system_logs():
    # get the admin nav links
    nav = admin_nav()

    # start with an empty list in case something goes wrong
    logs = []

    # try to get the logs from supabase
    # we use a try/except so the page doesnt crash if supabase is down
    try:
        # get a supabase client that uses the service role key
        # the service role key lets us read logs even if row level security is on
        client = _get_logger_client()

        # if client is None it means the secret key env var isnt set
        # in that case we just show an empty list
        if client is not None:
            # query the logs table
            # we ask for specific columns so we dont get extra stuff we dont need
            # order by created_at descending so newest logs come first
            # limit 5 so we only get the top 5
            result = (
                client.table("logs")
                .select("level, event_type, message, user_id, path, method, status_code, details, created_at")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )
            # result.data is a list of dicts, one dict per log row
            # if something weird happened and data is None, use empty list
            logs = result.data or []

    except Exception as err:
        # something went wrong talking to supabase
        # just print a warning and show an empty list
        print("WARNING: could not fetch logs from supabase - " + str(err))
        logs = []

    # render the logs page and pass the logs list to the template
    return render_page("System Logs", "admin", nav, "admin/logs.html", logs=logs)


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
