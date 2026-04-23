from api.ui_routes import ui_bp
from flask import redirect, request, url_for, jsonify
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    render_page,
    ui_login_required,
    user_nav,
)
from api.ui_routes.helpers import _resolve_app_base_url, _ui_user


@ui_bp.route("/me/token")
@ui_login_required
def get_token():
    # return the current session user's jwt so javascript can use it
    # to make authenticated calls to the rest api
    token = _ui_user().get("access_token")
    return jsonify({"token": token})


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    uid = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    providersList = []
    try:
        calDb = _get_ui_supabase_client()
        result = (
            calDb.table("externals")
            .select("id, provider, url")
            .eq("user_id", uid)
            .execute()
        )
        providersList = result.data or []
    except Exception as e:
        status = "error"
        message = f"Couldn't load external connections for uid {uid}: {e}"
    return render_page(
        "Manage Externals",
        "user",
        user_nav(),
        "user/externals.html",
        providers=providersList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    ownerId = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    records = []
    has_guest_link_fields = True
    calDb = None
    try:
        calDb = _get_ui_supabase_client()
        owned_result = (
            calDb.table("calendars")
            .select("id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active")
            .eq("owner_id", ownerId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        ownedRecs = owned_result.data or []
        member_result = (
            calDb.table("calendars")
            .select("id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active")
            .overlaps("member_ids", [ownerId])
            .order("age_timestamp", desc=False)
            .execute()
        )
        memberRecs = member_result.data or []
        records = []
        seenIds = []
        for c in ownedRecs:
            seenIds.append(c["id"])
            records.append(c)
        for c in memberRecs:
            if c["id"] not in seenIds:
                seenIds.append(c["id"])
                records.append(c)
    except Exception as e:
        if "guest_link_" in str(e):
            has_guest_link_fields = False
            try:
                if not calDb:
                    calDb = _get_ui_supabase_client()
                fb_owned = (
                    calDb.table("calendars")
                    .select("id, name, owner_id, member_ids, events")
                    .eq("owner_id", ownerId)
                    .order("age_timestamp", desc=False)
                    .execute()
                )
                fb_member = (
                    calDb.table("calendars")
                    .select("id, name, owner_id, member_ids, events")
                    .overlaps("member_ids", [ownerId])
                    .order("age_timestamp", desc=False)
                    .execute()
                )
                fbOwned = fb_owned.data or []
                fbMember = fb_member.data or []
                records = []
                fbSeen = []
                for c in fbOwned:
                    fbSeen.append(c["id"])
                    records.append(c)
                for c in fbMember:
                    if c["id"] not in fbSeen:
                        fbSeen.append(c["id"])
                        records.append(c)
                status = "error"
                message = "Guest links are unavailable because calendar guest-link columns are missing."
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


@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    userId = _ui_user()["id"]
    selected_calendar_id = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    calendars = []
    events = []
    try:
        calDb = _get_ui_supabase_client()
        owned_result = (
            calDb.table("calendars")
            .select("id, name")
            .eq("owner_id", userId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        ownedCals = owned_result.data or []
        member_result = (
            calDb.table("calendars")
            .select("id, name")
            .overlaps("member_ids", [userId])
            .order("age_timestamp", desc=False)
            .execute()
        )
        memberCals = member_result.data or []
        calendars = []
        seenIds = []
        for c in ownedCals:
            seenIds.append(c["id"])
            calendars.append(c)
        for c in memberCals:
            if c["id"] not in seenIds:
                seenIds.append(c["id"])
                calendars.append(c)
        if calendars:
            foundIt = False
            for c in calendars:
                if str(c.get("id")) == selected_calendar_id:
                    foundIt = True
                    break
            if not selected_calendar_id or foundIt == False:
                selected_calendar_id = str(calendars[0].get("id"))
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


@ui_bp.route("/user/events/<event_id>/edit")
@ui_login_required
def edit_event(event_id):
    # just load the event data and render the edit page
    # saving is handled by JS calling PUT /events/<id>
    uid = _ui_user()["id"]
    calDb = _get_ui_supabase_client()
    try:
        eventResult = (
            calDb.table("events")
            .select("id, title, description, start_timestamp, end_timestamp, calendar_ids, owner_id")
            .eq("id", event_id)
            .eq("owner_id", uid)
            .execute()
        )
        if len(eventResult.data) == 0:
            return redirect(url_for("ui.manage_events", status="error", message=f"Event {event_id} not found"))
        eventData = eventResult.data[0]
    except Exception as e:
        return redirect(url_for("ui.manage_events", status="error", message=f"Couldn't load event {event_id}: {e}"))
    return render_page(
        "Edit Event",
        "user",
        user_nav(),
        "user/events_edit.html",
        event=eventData,
        status="",
        message="",
    )


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    uid = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    friendsList = []
    try:
        calDb = _get_ui_supabase_client()
        userRow = calDb.table("users").select("friends").eq("id", uid).execute()
        if len(userRow.data) == 0:
            friendIds = []
        else:
            friendIds = userRow.data[0].get("friends") or []
        if len(friendIds) > 0:
            friendsResult = (
                calDb.table("users")
                .select("id, email, display_name")
                .in_("id", friendIds)
                .execute()
            )
            friendsList = friendsResult.data or []
    except Exception as e:
        status = "error"
        message = f"Couldn't load friends for uid {uid}: {e}"
    return render_page(
        "Manage Friends",
        "user",
        user_nav(),
        "user/friends.html",
        friends=friendsList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")
