from flask import redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    _ui_user,
    placeholder_externals,
    placeholder_friends,
    render_page,
    ui_login_required,
    user_nav,
)


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    return render_page("Manage Externals", "user", user_nav(), "user/externals.html",
                       providers=placeholder_externals)


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    owner_id = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    records = []
    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("calendars")
            .select("id, name, owner_id, member_ids, events")
            .eq("owner_id", owner_id)
            .order("age_timestamp", desc=False)
            .execute()
        )
        records = result.data or []
    except Exception as exc:
        status = "error"
        message = f"Failed to load calendars: {exc}"

    return render_page("Manage Calendars", "user", user_nav(), "user/calendars.html",
                       status=status, message=message, owner_id=owner_id, calendars=records)


@ui_bp.route("/user/calendars/create", methods=["POST"])
@ui_login_required
def create_calendar():
    name = (request.form.get("name") or "").strip()
    owner_id = _ui_user()["id"]

    if not owner_id or not name:
        return redirect(url_for(
            "ui.manage_calendars",
            status="error",
            message="Owner ID and calendar name are required.",
        ))

    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("calendars")
            .insert({"name": name, "owner_id": owner_id, "member_ids": [owner_id], "events": []})
            .execute()
        )
        created_id = (result.data or [{}])[0].get("id") or "new row"
        return redirect(url_for(
            "ui.manage_calendars",
            status="ok",
            message=f"Calendar created successfully (id: {created_id}).",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.manage_calendars",
            status="error",
            message=f"Failed to create calendar: {exc}",
        ))


@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    user_id = _ui_user()["id"]
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    calendars = []
    events = []

    try:
        supabase = _get_ui_supabase_client()
        calendars_result = (
            supabase.table("calendars")
            .select("id, name")
            .eq("owner_id", user_id)
            .order("age_timestamp", desc=False)
            .execute()
        )
        calendars = calendars_result.data or []

        if calendars:
            if not selected_calendar_id or not any(
                str(c.get("id")) == selected_calendar_id for c in calendars
            ):
                selected_calendar_id = str(calendars[0].get("id"))

            events_result = (
                supabase.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events = events_result.data or []
    except Exception as exc:
        status = "error"
        message = f"Failed to load events: {exc}"

    if not calendars:
        return render_page("Manage Events", "user", user_nav(), "user/events_no_calendars.html",
                           status=status, message=message)

    return render_page("Manage Events", "user", user_nav(), "user/events.html",
                       status=status, message=message,
                       calendars=calendars,
                       selected_calendar_id=selected_calendar_id,
                       events=events)


@ui_bp.route("/user/events/create", methods=["POST"])
@ui_login_required
def create_event_ui():
    user_id = _ui_user()["id"]
    calendar_id = (request.form.get("calendar_id") or "").strip()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    if not calendar_id or not title:
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="error",
            message="Calendar and title are required.",
        ))

    try:
        supabase = _get_ui_supabase_client()
        ownership = (
            supabase.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", user_id)
            .execute()
        )
        if not ownership.data:
            return redirect(url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="error",
                message="You do not have access to that calendar.",
            ))

        payload = {"title": title, "owner_id": user_id, "calendar_ids": [calendar_id]}
        if description:
            payload["description"] = description
        if start_timestamp:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp:
            payload["end_timestamp"] = end_timestamp

        result = supabase.table("events").insert(payload).execute()
        created_id = (result.data or [{}])[0].get("id") or "new row"
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="ok",
            message=f"Event created successfully (id: {created_id}).",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.manage_events",
            calendar_id=calendar_id,
            status="error",
            message=f"Failed to create event: {exc}",
        ))


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    return render_page("Manage Friends", "user", user_nav(), "user/friends.html",
                       friends=placeholder_friends)


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")
