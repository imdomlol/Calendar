import traceback
import logging
from flask import redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import guest_nav, render_page
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def _resolve_shared_calendar(token):
    supabase = get_supabase_client()
    result = (
        supabase.table("calendars")
        .select(
            "id, name, owner_id, guest_link_token, guest_link_role, guest_link_active"
        )
        .eq("guest_link_token", token)
        .eq("guest_link_active", "true")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    return rows[0]


def _load_calendar_events(calendar_id):
    # this function gets all the events for a calendar
    # we pass in calendar_id to know which one to look for
    # first get the supabase client so we can connect to the database
    supabase = get_supabase_client()
    # now we query the events table
    # overlaps checks if the calendar_ids array contains our id
    # we also order by start time so events appear in order
    result = (
        supabase.table("events")
        .select("id, title, description, start_timestamp, end_timestamp")
        .overlaps("calendar_ids", [str(calendar_id)])
        .order("start_timestamp", desc=False)
        .execute()
    )
    # result.data is the list or None so we use or [] to always get a list back
    eventsData = result.data or []
    # return the events list to whoever called this
    return eventsData




def _get_editor_calendar(token):
    # look up the calendar for this token
    calRow = _resolve_shared_calendar(token)
    if not calRow:
        return None, redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message="Share link is invalid or inactive.",
            )
        )
    role = str(calRow.get("guest_link_role") or "viewer").lower()
    if role != "editor": #only editor links can make changes
        return None, redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message="This share link is view-only.",
            )
        )
    return calRow, None

@ui_bp.route("/guest/<token>")
def public_calendar(token):
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    try:
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            return render_page(
                "Shared Calendar", "guest", guest_nav(), "guest/not_found.html"
            )

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
    except Exception as exc:
        logger.error(
            "public_calendar: unhandled exception for token %r — %s: %s\n%s",
            token,
            type(exc).__name__,
            exc,
            traceback.format_exc(),
        )
        try:
            return render_page(
                "Shared Calendar",
                "guest",
                guest_nav(),
                "guest/not_found.html",
                message="Could not load the shared calendar. The link may be invalid or a server error occurred.",
            )
        except Exception:
            logger.error("public_calendar: fallback render also failed:\n%s", traceback.format_exc())
            from flask import make_response
            return make_response(
                "<h1>Shared Calendar Unavailable</h1><p>An error occurred. Please try again later.</p>",
                500,
            )



@ui_bp.route("/guest/<token>/events/create", methods=["POST"])
def public_create_event(token):
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    # check if title field was left empty
    if len(title) == 0:
        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message="Title is required.",
            )
        )

    try:
        cal_row, err = _get_editor_calendar(token)
        if err:
            return err

        # owner_id is the calendar owner so events show under the right account
        pload = {
            "title": title,
            "owner_id": cal_row.get("owner_id"),
            "calendar_ids": [str(cal_row.get("id"))],
        }
        if description:
            pload["description"] = description
        if start_timestamp:
            pload["start_timestamp"] = start_timestamp
        if end_timestamp:
            pload["end_timestamp"] = end_timestamp

        supabase = get_supabase_client()
        supabase.table("events").insert(pload).execute()

        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="ok",
                message="Event created successfully.",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message=f"Failed to create event: {exc}",
            )
        )


@ui_bp.route("/guest/<token>/events/<event_id>/edit", methods=["POST"])
def public_edit_event(token, event_id):
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    try:
        calRow, err = _get_editor_calendar(token)
        if err:
            return err

        calId = str(calRow.get("id"))
        supabase = get_supabase_client()

        # confirm the event is part of this calendar before allowing edits
        existing = (
            supabase.table("events")
            .select("id")
            .eq("id", event_id)
            .overlaps("calendar_ids", [calId])
            .limit(1)
            .execute()
        )
        if not (existing.data or []):
            return redirect(
                url_for(
                    "ui.public_calendar",
                    token=token,
                    status="error",
                    message="Event not found for this shared calendar.",
                )
            )

        updates = {
            # optional fields are always included so guests can clear them by submitting blank
            "description": description or None,
            "start_timestamp": start_timestamp or None,
            "end_timestamp": end_timestamp or None,
        }
        if title:
            updates["title"] = title

        supabase.table("events").update(updates).eq("id", event_id).execute()

        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="ok",
                message="Event updated successfully.",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message=f"Failed to update event: {exc}",
            )
        )

@ui_bp.route("/guest/<token>/events/<event_id>/delete", methods=["POST"])
def public_delete_event(token, event_id):
    try:
        calendar_row, err = _get_editor_calendar(token)
        if err:
            return err

        calendar_id = str(calendar_row.get("id"))
        supabase = get_supabase_client()

        # make sure the event belongs to this calendar before deleting
        existing = (
            supabase.table("events")
            .select("id")
            .eq("id", event_id)
            .overlaps("calendar_ids", [calendar_id])
            .limit(1)
            .execute()
        )
        if not (existing.data or []):
            return redirect(
                url_for(
                    "ui.public_calendar",
                    token=token,
                    status="error",
                    message="Event not found for this shared calendar.",
                )
            )

        supabase.table("events").delete().eq("id", event_id).execute()

        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="ok",
                message="Event deleted successfully.",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.public_calendar",
                token=token,
                status="error",
                message=f"Failed to delete event: {exc}",
            )
        )
