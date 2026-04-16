from flask import redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import guest_nav, render_page
from utils.supabase_client import get_supabase_client


def _resolve_shared_calendar(token):
    supabase = get_supabase_client()
    result = (
        supabase.table("calendars")
        .select("id, name, owner_id, guest_link_token, guest_link_role, guest_link_active")
        .eq("guest_link_token", token)
        .eq("guest_link_active", True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    return rows[0]


def _load_calendar_events(calendar_id):
    supabase = get_supabase_client()
    result = (
        supabase.table("events")
        .select("id, title, description, start_timestamp, end_timestamp")
        .overlaps("calendar_ids", [str(calendar_id)])
        .order("start_timestamp", desc=False)
        .execute()
    )
    return result.data or []


@ui_bp.route("/guest/<token>")
def public_calendar(token):
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    try:
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            return render_page("Shared Calendar", "guest", guest_nav(), "public/not_found.html")

        events = _load_calendar_events(calendar_row.get("id"))
        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        can_edit = role == "editor"

        return render_page(
            "Shared Calendar",
            "guest",
            guest_nav(),
            "public/calendar.html",
            token=token,
            calendar=calendar_row,
            events=events,
            status=status,
            message=message,
            can_edit=can_edit,
        )
    except Exception as exc:
        return render_page(
            "Shared Calendar",
            "guest",
            guest_nav(),
            "public/not_found.html",
            message=f"Could not load shared calendar: {exc}",
        )


@ui_bp.route("/guest/<token>/events/create", methods=["POST"])
def public_create_event(token):
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    if not title:
        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="error",
            message="Title is required.",
        ))

    try:
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="Share link is invalid or inactive."))

        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        if role != "editor":
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="This share link is view-only."))

        payload = {
            "title": title,
            "owner_id": calendar_row.get("owner_id"),
            "calendar_ids": [str(calendar_row.get("id"))],
        }
        if description:
            payload["description"] = description
        if start_timestamp:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp:
            payload["end_timestamp"] = end_timestamp

        supabase = get_supabase_client()
        supabase.table("events").insert(payload).execute()

        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="ok",
            message="Event created successfully.",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="error",
            message=f"Failed to create event: {exc}",
        ))


@ui_bp.route("/guest/<token>/events/<event_id>/edit", methods=["POST"])
def public_edit_event(token, event_id):
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    try:
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="Share link is invalid or inactive."))

        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        if role != "editor":
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="This share link is view-only."))

        calendar_id = str(calendar_row.get("id"))
        supabase = get_supabase_client()

        existing = (
            supabase.table("events")
            .select("id")
            .eq("id", event_id)
            .overlaps("calendar_ids", [calendar_id])
            .limit(1)
            .execute()
        )
        if not (existing.data or []):
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="Event not found for this shared calendar."))

        updates = {}
        if title:
            updates["title"] = title
        updates["description"] = description if description else None
        updates["start_timestamp"] = start_timestamp if start_timestamp else None
        updates["end_timestamp"] = end_timestamp if end_timestamp else None

        if not updates:
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="No event changes were provided."))

        supabase.table("events").update(updates).eq("id", event_id).execute()

        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="ok",
            message="Event updated successfully.",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="error",
            message=f"Failed to update event: {exc}",
        ))


@ui_bp.route("/guest/<token>/events/<event_id>/delete", methods=["POST"])
def public_delete_event(token, event_id):
    try:
        calendar_row = _resolve_shared_calendar(token)
        if not calendar_row:
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="Share link is invalid or inactive."))

        role = str(calendar_row.get("guest_link_role") or "viewer").lower()
        if role != "editor":
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="This share link is view-only."))

        calendar_id = str(calendar_row.get("id"))
        supabase = get_supabase_client()

        existing = (
            supabase.table("events")
            .select("id")
            .eq("id", event_id)
            .overlaps("calendar_ids", [calendar_id])
            .limit(1)
            .execute()
        )
        if not (existing.data or []):
            return redirect(url_for("ui.public_calendar", token=token, status="error", message="Event not found for this shared calendar."))

        supabase.table("events").delete().eq("id", event_id).execute()

        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="ok",
            message="Event deleted successfully.",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.public_calendar",
            token=token,
            status="error",
            message=f"Failed to delete event: {exc}",
        ))
