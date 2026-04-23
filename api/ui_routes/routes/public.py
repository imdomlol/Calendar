import logging
import traceback
from flask import request
from api.ui_routes import ui_bp
from api.ui_routes.helpers import guest_nav, render_page
from utils.supabase_client import get_supabase_client

calLogger = logging.getLogger(__name__)


def _resolve_shared_calendar(token):
    # look up a calendar by its guest link token
    # returns the calendar row or None if not found or inactive
    calDb = get_supabase_client()
    result = (
        calDb.table("calendars")
        .select(
            "id, name, owner_id, guest_link_token, guest_link_role, guest_link_active"
        )
        .eq("guest_link_token", token)
        .eq("guest_link_active", "true")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if len(rows) == 0:
        return None
    # return the first row since we limit to 1
    return rows[0]


def _load_calendar_events(calendar_id):
    # this function gets all the events for a calendar
    # we pass in calendar_id to know which one to look for
    # first get the supabase client so we can connect to the database
    calDb = get_supabase_client()
    # now we query the events table
    # overlaps checks if the calendar_ids array contains our id
    # we also order by start time so events appear in order
    result = (
        calDb.table("events")
        .select("id, title, description, start_timestamp, end_timestamp")
        .overlaps("calendar_ids", [str(calendar_id)])
        .order("start_timestamp", desc=False)
        .execute()
    )
    # result.data is the list or None so we use or [] to always get a list back
    eventsData = result.data or []
    # return the events list to whoever called this
    return eventsData





@ui_bp.route("/guest/<token>")
def public_calendar(token):
    # get status and message from query params if they were redirected here
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    try:
        # look up the calendar by the token
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            # token didn't match any active calendar
            return render_page(
                "Shared Calendar", "guest", guest_nav(), "guest/not_found.html"
            )

        # get the events and figure out the role for this link
        events = _load_calendar_events(calendar_row.get("id"))
        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        can_edit = role == "editor" #true if this is an editor link

        return render_page(
            "Shared Calendar",
            "guest",
            guest_nav(),
            "guest/calendar.html",
            token=token,
            calendar=calendar_row,
            events=events,
            status=status,
            message=message,
            can_edit=can_edit,
        )
    except Exception as err:
        calLogger.error(
            "public_calendar: unhandled exception for token %r — %s: %s\n%s",
            token,
            type(err).__name__,
            err,
            traceback.format_exc(),
        )
        try:
            return render_page(
                "Shared Calendar",
                "guest",
                guest_nav(),
                "guest/not_found.html",
                message="Couldn't load shared calendar, link may be invalid",
            )
        except Exception:
            calLogger.error("public_calendar: fallback render also failed:\n%s", traceback.format_exc())
            from flask import make_response
            return make_response(
                "<h1>Shared Calendar Unavailable</h1><p>An error occurred. Please try again later.</p>",
                500,
            )



