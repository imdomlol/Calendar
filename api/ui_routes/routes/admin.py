from api.ui_routes.helpers import render_page, ui_login_required
from api.ui_routes import ui_bp

from api.ui_routes.helpers import admin_nav, placeholder_externals, placeholder_logs


# this is the route that shows system logs for admins
@ui_bp.route("/admin/logs")
@ui_login_required
def system_logs():
    # first we need to get the nav for the admin section
    # admin_nav is a function that returns the nav links
    # we save it to nav so we can pass it in later
    nav = admin_nav()
    # these are the logs we will show on the page
    # its just placeholder data for now until real queries are added
    # we store it in logData
    logData = placeholder_logs
    # now call render_page to build the html response
    # first arg is the title
    # second is the role which is admin
    # third is the nav we got above
    # fourth is the template file
    # and we pass the logs too
    return render_page("System Logs", "admin", nav, "admin/logs.html",
                       logs=logData)

@ui_bp.route("/admin/notifications")
@ui_login_required
def send_notification():
    return render_page("Notifications", "admin", admin_nav(), "admin/notification.html")




@ui_bp.route("/admin/suspend")
@ui_login_required
def suspend_user():
    navData = admin_nav() #admin nav
    return render_page("Suspend User", "admin", navData, "admin/suspend.html")


@ui_bp.route("/admin/unlink")
@ui_login_required
def admin_unlink():
    # get providers list for unlink page
    provs = placeholder_externals
    return render_page("Unlink External Calendars", "admin", admin_nav(), "admin/unlink.html",
                       providers=provs)
