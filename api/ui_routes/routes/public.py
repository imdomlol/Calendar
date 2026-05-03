import logging
import traceback
from flask import make_response, request
from api.ui_routes import ui_bp
from api.ui_routes.helpers import render_page
from models.calendar import Calendar

cal_logger = logging.getLogger(__name__)


# ========================= Shared Calendar Page =========================


@ui_bp.route("/guest/<token>")
def public_calendar(token):
    # show a shared calendar from a guest token
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    try:
        # find the calendar tied to this guest link
        calendar_row = Calendar.find_by_guest_token(token)
        if not calendar_row:
            return render_page("Shared Calendar", "guest/not_found.html")

        # load events after the token is confirmed
        events = Calendar.list_events(calendar_row.get("id"))
        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        can_edit = role == "editor"

        return render_page(
            "Shared Calendar",
            "guest/calendar.html",
            token=token,
            calendar=calendar_row,
            events=events,
            status=status,
            message=message,
            can_edit=can_edit,
        )
    except Exception as err:
        # keep a full error log so bad links are easier to debug
        cal_logger.error(
            "public_calendar: unhandled exception for token %r — %s: %s\n%s",
            token,
            type(err).__name__,
            err,
            traceback.format_exc(),
        )
        try:
            # use the normal missing page when the main page fails
            return render_page(
                "Shared Calendar",
                "guest/not_found.html",
                message="Couldn't load shared calendar, link may be invalid",
            )
        except Exception:
            # return plain HTML if templates are also broken
            cal_logger.error(
                "public_calendar: fallback render also failed:\n%s",
                traceback.format_exc(),
            )
            return make_response(
                "<h1>Shared Calendar Unavailable</h1><p>An error occurred. Please try again later.</p>",
                500,
            )
