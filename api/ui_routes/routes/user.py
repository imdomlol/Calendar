from api.ui_routes import ui_bp
from flask import redirect, request, url_for
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    render_page,
    ui_login_required,
    user_nav,
)
from api.ui_routes.helpers import _resolve_app_base_url, _ui_user, placeholder_externals, placeholder_friends
import secrets


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
    calDb = None
    try:
        calDb = _get_ui_supabase_client()
        result = (
            calDb.table("calendars")
            .select(
                "id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active"
            )
            .eq("owner_id", ownerId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        records = result.data or []
    except Exception as e:
        # handle the case where guest link columns dont exist yet
        if "guest_link_" in str(e):
            has_guest_link_fields = False
            try:
                if not calDb:
                    calDb = _get_ui_supabase_client()
                fallback = (
                    calDb.table("calendars")
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
            except Exception as fallback_err:
                status = "error"
                message = f"fallback query failed for owner {ownerId}: {fallback_err}"
        else:
            status = "error"
            message = f"Couldn't load calendars for owner {ownerId}: {e}"

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
    # get the calendar name from the form
    calName = (request.form.get("name") or "").strip()
    ownerId = _ui_user()["id"]

    # make sure they actually typed a name
    if not calName:
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message="Calendar name is required",
            )
        )

    try:
        calDb = _get_ui_supabase_client()
        result = (
            calDb.table("calendars")
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
        # get the id from the result so we can include it in the success message
        created_id = (result.data or [{}])[0].get("id") or "new row"
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="ok",
                message=f"Calendar created (id: {created_id}).",
            )
        )
    except Exception as err:
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"create calendar failed for owner {ownerId}: {err}",
            )
        )


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["POST"])
@ui_login_required
def create_guest_link(calendar_id):
    # get the user id and the role they want for the link
    userId = _ui_user()["id"]
    role = (request.form.get("role") or "viewer").strip().lower()
    # only viewer and editor are valid roles
    if role not in {"viewer", "editor"}:
        role = "viewer"

    # token_urlsafe(24) gives a 32 char url safe base64 string
    tok = secrets.token_urlsafe(24)

    try:
        calDb = _get_ui_supabase_client()
        # check that the user owns this calendar before creating a link
        ownership = (
            calDb.table("calendars")
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
                    message=f"Calendar {calendar_id} not owned by uid {userId}",
                )
            )

        # save the token and role to the calendar row
        calDb.table("calendars").update(
            {
                "guest_link_token": tok,
                "guest_link_role": role,
                "guest_link_active": True,
            }
        ).eq("id", calendar_id).eq("owner_id", userId).execute()

        # build the full guest url to include in the success message
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
                message=f"guest link failed for calendar {calendar_id}: {text}",
            )
        )


@ui_bp.route("/user/calendars/<calendar_id>/guest-link/revoke", methods=["POST"])
@ui_login_required
def revoke_guest_link(calendar_id):
    # get the user id to verify ownership
    uid = _ui_user()["id"]

    try:
        calDb = _get_ui_supabase_client()
        # check ownership before revoking
        ownership = (
            calDb.table("calendars")
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
                    message=f"Calendar {calendar_id} not owned by uid {uid}",
                )
            )

        # clear the guest link fields to revoke it
        calDb.table("calendars").update(
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
                message="Guest link revoked.",
            )
        )
    except Exception as e:
        text = str(e)
        if "guest_link_" in text:
            text = (
                "Guest-link columns are missing on calendars. "
                "Add guest_link_token, guest_link_role, and guest_link_active first."
            )
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"revoke failed for calendar {calendar_id}: {text}",
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

    # these will be filled in below
    calendars = []
    events = []

    try:
        calDb = _get_ui_supabase_client()
        # get the user's calendars so we can show a dropdown
        calendars_result = (
            calDb.table("calendars")
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
            # if no match fall back to first calendar
            if not selected_calendar_id or foundIt == False:
                selected_calendar_id = str(calendars[0].get("id"))

            # now get the events for the selected calendar
            events_result = (
                calDb.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events = events_result.data or []
    except Exception as err:
        status = "error"
        message = f"Couldn't load events for uid {userId}: {err}"

    # if the user has no calendars show a different page
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
    # get the user id and all the form fields
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
        calDb = _get_ui_supabase_client()
        # check the user actually owns the calendar they are adding to
        ownership = (
            calDb.table("calendars")
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
                    message=f"Calendar {calendar_id} not owned by uid {uid}",
                )
            )

        # build the payload and add optional fields if they are not empty
        payload = {"title": title, "owner_id": uid, "calendar_ids": [calendar_id]}
        if description:
            payload["description"] = description
        if start_timestamp:
            payload["start_timestamp"] = start_timestamp
        if end_timestamp:
            payload["end_timestamp"] = end_timestamp

        result = calDb.table("events").insert(payload).execute()
        created_id = (result.data or [{}])[0].get("id") or "new row" #get id from result
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="ok",
                message=f"Event created (id: {created_id}).",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendar_id,
                status="error",
                message=f"create event failed for uid {uid}: {exc}",
            )
        )



@ui_bp.route("/user/calendars/<calendar_id>/delete", methods=["POST"])
@ui_login_required
def delete_calendar(calendar_id):
    # first get the logged in users id
    # we need it to check they own the calendar before deleting
    uid = _ui_user()["id"]

    try:
        calDb = _get_ui_supabase_client()

        # check that this calendar actually belongs to the user
        # we can't just trust the calendar_id from the url
        # someone could put any id in there and try to delete someone elses calendar
        ownerCheck = (
            calDb.table("calendars")
            .select("id")
            .eq("id", calendar_id)
            .eq("owner_id", uid)
            .execute()
        )

        # if the data list is empty that means no matching calendar was found for this owner
        # so we stop here and show an error
        if len(ownerCheck.data) == 0:
            return redirect(
                url_for(
                    "ui.manage_calendars",
                    status="error",
                    message=f"Calendar {calendar_id} not owned by uid {uid}",
                )
            )

        # ok the user owns it so we can delete it now
        # we still add the owner_id check to the delete just to be safe
        calDb.table("calendars").delete().eq("id", calendar_id).eq("owner_id", uid).execute()

        # redirect back to the calendars page with a success message
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="ok",
                message=f"Calendar {calendar_id} deleted.",
            )
        )
    except Exception as err:
        # something went wrong with supabase so show the error
        return redirect(
            url_for(
                "ui.manage_calendars",
                status="error",
                message=f"delete calendar failed for calendar {calendar_id}: {err}",
            )
        )


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    # show the friends management page
    # uses placeholder friends data for now
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
    # show the remove account confirmation page
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")
