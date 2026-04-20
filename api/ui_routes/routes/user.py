import secrets
from api.ui_routes import ui_bp
from flask import redirect, request, url_for

from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    render_page,
    ui_login_required,
    user_nav,
)
from api.ui_routes.helpers import _resolve_app_base_url, _ui_user, placeholder_externals, placeholder_friends


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    # this route shows the manage externals page
    # it is for managing external calendar connections
    # first we get the providers list
    # placeholder_externals is just test data for now
    provs = placeholder_externals
    # now we render the page
    # we pass provs as the providers keyword arg
    return render_page(
        "Manage Externals",
        "user",
        user_nav(),
        "user/externals.html",
        providers=provs,
    )

@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    """Loads owned calendars with guest link status; falls back without guest link fields if migration has not run."""
    ownerId = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    records = []
    has_guest_link_fields = True
    supabase = None
    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("calendars")
            .select(
                "id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active"
            )
            .eq("owner_id", ownerId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        records = result.data or []
    except Exception as exc:
        # handle the case where guest link columns dont exist yet
        if "guest_link_" in str(exc):
            has_guest_link_fields = False
            try:
                if not supabase:
                    supabase = _get_ui_supabase_client()
                fallback = (
                    supabase.table("calendars")
                    .select("id, name, owner_id, member_ids, events")
                    .eq("owner_id", ownerId)
                    .order("age_timestamp", desc=False)
                    .execute()
                )
                records = fallback.data or []
                status = "error"
                message = (
                    "Guest links are unavailable because calendar guest-link columns are missing. "
                    "Add guest_link_token, guest_link_role, and guest_link_active to calendars."
                )
            except Exception as fallback_exc:
                status = "error"
                message = f"Failed to load calendars: {fallback_exc}"
        else:
            status = "error"
            message = f"Failed to load calendars: {exc}"

    return render_page(
        "Manage Calendars",
        "user",
        user_nav(),
        "user/calendars.html",
        status=status,
        message=message,
        owner_id=ownerId,
        calendars=records,
        has_guest_link_fields=has_guest_link_fields,
        app_base_url=_resolve_app_base_url(),
    )



@ui_bp.route("/user/calendars/create", methods=["POST"])
@ui_login_required
def create_calendar():
    calName = (request.form.get("name") or "").strip()
    ownerId = _ui_user()["id"]

    if not calName:
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message="Calendar name is required.",
            )
        )

    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("calendars")
            .insert(
                {
                    "name": calName,
                    "owner_id": ownerId,
                    "member_ids": [ownerId],
                    "events": [],
                }
            )
            .execute()
        )
        created_id = (result.data or [{}])[0].get("id") or "new row"
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="ok",
                message=f"Calendar created successfully (id: {created_id}).",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"Failed to create calendar: {exc}",
            )
        )


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["POST"])
@ui_login_required
def create_guest_link(calendar_id):
    userId = _ui_user()["id"]
    role = (request.form.get("role") or "viewer").strip().lower()
    if role not in {"viewer", "editor"}:
        role = "viewer"

    # token_urlsafe(24) gives a 32 char url safe base64 string
    tok = secrets.token_urlsafe(24)

    try:
        supabase = _get_ui_supabase_client()
        ownership = (
            supabase.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", userId)
            .execute()
        )
        if not ownership.data:
            return redirect(
                url_for(
                    "ui.manage_calendars",
                    status="error",
                    message="You do not have access to that calendar.",
                )
            )

        supabase.table("calendars").update(
            {
                "guest_link_token": tok,
                "guest_link_role": role,
                "guest_link_active": True,
            }
        ).eq("id", calendar_id).eq("owner_id", userId).execute()

        guest_url = (
            f"{_resolve_app_base_url()}{url_for('ui.public_calendar', token=tok)}"
        )
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="ok",
                message=f"Guest link generated ({role}). URL: {guest_url}",
            )
        )
    except Exception as exc:
        text = str(exc)
        if "guest_link_" in text:
            text = (
                "Guest-link columns are missing on calendars. "
                "Add guest_link_token, guest_link_role, and guest_link_active first."
            )
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"Failed to generate guest link: {text}",
            )
        )




@ui_bp.route("/user/calendars/<calendar_id>/guest-link/revoke", methods=["POST"])
@ui_login_required
def revoke_guest_link(calendar_id):
    uid = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()
        ownership = (
            supabase.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", uid)
            .execute()
        )
        if not ownership.data:
            return redirect(
                url_for(
                    "ui.manage_calendars",
                    status="error",
                    message="You do not have access to that calendar.",
                )
            )

        supabase.table("calendars").update(
            {
                "guest_link_token": None,
                "guest_link_role": None,
                "guest_link_active": False,
            }
        ).eq("id", calendar_id).eq("owner_id", uid).execute()

        return redirect(
            url_for(
                "ui.manage_calendars",
                status="ok",
                message="Guest link revoked successfully.",
            )
        )
    except Exception as exc:
        text = str(exc)
        if "guest_link_" in text:
            text = (
                "Guest-link columns are missing on calendars. "
                "Add guest_link_token, guest_link_role, and guest_link_active first."
            )
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"Failed to revoke guest link: {text}",
            )
        )

@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    """Shows events for a selected calendar; defaults to the first calendar if none is specified in query params."""
    userId = _ui_user()["id"]
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
            .eq("owner_id", userId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        calendars = calendars_result.data or []

        if calendars:
            # check if the requested calendar id is in the list
            foundIt = False
            for c in calendars:
                if str(c.get("id")) == selected_calendar_id:
                    foundIt = True
                    break
            if not selected_calendar_id or foundIt == False:
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
        return render_page(
            "Manage Events",
            "user",
            user_nav(),
            "user/events_no_calendars.html",
            status=status,
            message=message,
        )

    return render_page(
        "Manage Events",
        "user",
        user_nav(),
        "user/events.html",
        status=status,
        message=message,
        calendars=calendars,
        selected_calendar_id=selected_calendar_id,
        events=events,
    )


@ui_bp.route("/user/events/create", methods=["POST"])
@ui_login_required
def create_event():
    uid = _ui_user()["id"]
    calendar_id = (request.form.get("calendar_id") or "").strip()
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    # make sure we have both a calendar and a title before doing anything
    if len(calendar_id) == 0 or len(title) == 0:
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="error",
                message="Calendar and title are required.",
            )
        )

    try:
        supabase = _get_ui_supabase_client()
        ownership = (
            supabase.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", uid)
            .execute()
        )
        if not ownership.data:
            return redirect(
                url_for(
                    "ui.manage_events",
                    calendar_id=calendar_id,
                    status="error",
                    message="You do not have access to that calendar.",
                )
            )

        payload = {"title": title, "owner_id": uid, "calendar_ids": [calendar_id]}
        if description:
            payload["description"] = description
        if start_timestamp:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp:
            payload["end_timestamp"] = end_timestamp

        result = supabase.table("events").insert(payload).execute()
        created_id = (result.data or [{}])[0].get("id") or "new row" #get id from result
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="ok",
                message=f"Event created successfully (id: {created_id}).",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="error",
                message=f"Failed to create event: {exc}",
            )
        )



@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    return render_page(
        "Manage Friends",
        "user",
        user_nav(),
        "user/friends.html",
        friends=placeholder_friends,
    )

@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")
