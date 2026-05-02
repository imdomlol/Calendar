import logging
import traceback
from flask import make_response, request
from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page
from models.calendar import Calendar

calLogger = logging.getLogger(__name__)


@ui_bp.route("/guest/<token>")
def public_calendar(token):
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    try:
        calendar_row = Calendar.findByGuestToken(token)
        if not calendar_row:
            return render_page("Shared Calendar", "guest/not_found.html")

        events = Calendar.listEvents(calendar_row.get("id"))
        role = str(calendar_row.get("guest_link_role") or "viewer").lower()

        return render_page(
            "Shared Calendar", "guest/calendar.html",
            token=token,
            calendar=calendar_row,
            events=events,
            status=status,
            message=message,
            can_edit=role == "editor",
        )
    except Exception as err:
        calLogger.error(
            "public_calendar: unhandled exception for token %r — %s: %s\n%s",
            token, type(err).__name__, err, traceback.format_exc(),
        )
        try:
            return render_page("Shared Calendar", "guest/not_found.html",
                               message="Couldn't load shared calendar, link may be invalid")
        except Exception:
            calLogger.error("public_calendar: fallback render also failed:\n%s", traceback.format_exc())
            return make_response(
                "<h1>Shared Calendar Unavailable</h1><p>An error occurred. Please try again later.</p>",
                500,
            )
