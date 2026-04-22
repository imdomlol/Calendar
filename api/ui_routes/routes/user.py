from api.ui_routes import ui_bp
from flask import redirect, request, url_for
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    render_page,
    ui_login_required,
    user_nav,
)
from api.ui_routes.helpers import _resolve_app_base_url, _ui_user
import secrets


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    # get the user id from the session
    uid = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    # this will hold the list of connected providers from the database
    providersList = []

    try:
        calDb = _get_ui_supabase_client()

        # load all external connections for this user
        # we only need id, provider, and url to display them
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
    """Loads owned calendars with guest link status; falls back without guest link fields if migration has not run."""
    ownerId = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    records = []
    has_guest_link_fields = True
    calDb = None
    try:
        calDb = _get_ui_supabase_client()

        # first get the calendars this user owns
        owned_result = (
            calDb.table("calendars")
            .select(
                "id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active"
            )
            .eq("owner_id", ownerId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        ownedRecs = owned_result.data or []

        # then get calendars where the user is a member but not the owner
        member_result = (
            calDb.table("calendars")
            .select(
                "id, name, owner_id, member_ids, events, guest_link_token, guest_link_role, guest_link_active"
            )
            .overlaps("member_ids", [ownerId])
            .order("age_timestamp", desc=False)
            .execute()
        )
        memberRecs = member_result.data or []

        # merge the two lists without duplicates
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
        # handle the case where guest link columns don't exist yet
        if "guest_link_" in str(e):
            has_guest_link_fields = False
            try:
                if not calDb:
                    calDb = _get_ui_supabase_client()

                # fallback owned query without guest link fields
                fb_owned = (
                    calDb.table("calendars")
                    .select("id, name, owner_id, member_ids, events")
                    .eq("owner_id", ownerId)
                    .order("age_timestamp", desc=False)
                    .execute()
                )
                # fallback member query without guest link fields
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
        # get owned calendars first
        owned_result = (
            calDb.table("calendars")
            .select("id, name")
            .eq("owner_id", userId)
            .order("age_timestamp", desc=False)
            .execute()
        )
        ownedCals = owned_result.data or []

        # also get calendars where the user is a member
        member_result = (
            calDb.table("calendars")
            .select("id, name")
            .overlaps("member_ids", [userId])
            .order("age_timestamp", desc=False)
            .execute()
        )
        memberCals = member_result.data or []

        # combine without duplicates
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


@ui_bp.route("/user/events/<event_id>/edit", methods=["GET", "POST"])
@ui_login_required
def edit_event(event_id):
    # get the user id from the session
    uid = _ui_user()["id"]

    calDb = _get_ui_supabase_client()

    if request.method == "GET":
        # we need to load the event so we can prefill the form
        # also need to check the user actually owns it
        try:
            eventResult = (
                calDb.table("events")
                .select("id, title, description, start_timestamp, end_timestamp, calendar_ids, owner_id")
                .eq("id", event_id)
                .eq("owner_id", uid)
                .execute()
            )
            # if nothing came back then either it doesn't exist or they don't own it
            if len(eventResult.data) == 0:
                return redirect(
                    url_for(
                        "ui.manage_events",
                        status="error",
                        message=f"Event {event_id} not found for uid {uid}",
                    )
                )
            eventData = eventResult.data[0]
        except Exception as e:
            return redirect(
                url_for(
                    "ui.manage_events",
                    status="error",
                    message=f"Couldn't load event {event_id}: {e}",
                )
            )

        # also load the users calendars so we can show a calendar picker on the form
        calendarsList = []
        try:
            calsResult = (
                calDb.table("calendars")
                .select("id, name")
                .eq("owner_id", uid)
                .execute()
            )
            calendarsList = calsResult.data or []
        except Exception as err:
            # not a fatal error, we can still show the form without the picker
            pass

        return render_page(
            "Edit Event",
            "user",
            user_nav(),
            "user/events_edit.html",
            event=eventData,
            calendars=calendarsList,
        )

    # POST - save the changes
    # get all the form fields
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    start_timestamp = (request.form.get("start_timestamp") or "").strip()
    end_timestamp = (request.form.get("end_timestamp") or "").strip()

    # title is the only required field
    if len(title) == 0:
        return redirect(
            url_for(
                "ui.edit_event",
                event_id=event_id,
            )
        )

    try:
        # first verify ownership before updating
        # same check as the GET so people can't edit events they don't own
        ownerCheck = (
            calDb.table("events")
            .select("id")
            .eq("id", event_id)
            .eq("owner_id", uid)
            .execute()
        )
        if len(ownerCheck.data) == 0:
            return redirect(
                url_for(
                    "ui.manage_events",
                    status="error",
                    message=f"Event {event_id} not owned by uid {uid}",
                )
            )

        # build the update payload
        # only include timestamp fields if they have a value
        updatePayload = {"title": title, "description": description}
        if start_timestamp:
            updatePayload["start_timestamp"] = start_timestamp
        if end_timestamp:
            updatePayload["end_timestamp"] = end_timestamp

        calDb.table("events").update(updatePayload).eq("id", event_id).eq("owner_id", uid).execute()

        return redirect(
            url_for(
                "ui.manage_events",
                status="ok",
                message=f"Event {event_id} updated.",
            )
        )
    except Exception as exc:
        return redirect(
            url_for(
                "ui.manage_events",
                status="error",
                message=f"edit event failed for event {event_id}: {exc}",
            )
        )


@ui_bp.route("/user/events/<event_id>/delete", methods=["POST"])
@ui_login_required
def delete_event(event_id):
    # grab the logged in user id
    uid = _ui_user()["id"]
    # we also need to know which calendar to go back to after deleting
    # the form sends it as a hidden field
    calendarId = (request.form.get("calendar_id") or "").strip()

    try:
        calDb = _get_ui_supabase_client()

        # check that this event belongs to the user before we delete it
        # we dont want someone deleting events they dont own
        ownerCheck = (
            calDb.table("events")
            .select("id")
            .eq("id", event_id)
            .eq("owner_id", uid)
            .execute()
        )

        # if the list is empty the event either doesnt exist or belongs to someone else
        if len(ownerCheck.data) == 0:
            return redirect(
                url_for(
                    "ui.manage_events",
                    calendar_id=calendarId,
                    status="error",
                    message=f"Event {event_id} not found for uid {uid}",
                )
            )

        # ok to delete now
        calDb.table("events").delete().eq("id", event_id).eq("owner_id", uid).execute()

        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendarId,
                status="ok",
                message=f"Event {event_id} deleted.",
            )
        )
    except Exception as e:
        return redirect(
            url_for(
                "ui.manage_events",
                calendar_id=calendarId,
                status="error",
                message=f"delete event failed for event {event_id}: {e}",
            )
        )


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    # get the logged in users id
    uid = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    friendsList = []

    try:
        calDb = _get_ui_supabase_client()

        # first load the current users row to get their friends array
        # the friends array is just a list of user ids
        userRow = (
            calDb.table("users")
            .select("friends")
            .eq("id", uid)
            .execute()
        )

        # if the user doesnt have a row in the users table yet just show empty list
        if len(userRow.data) == 0:
            friendIds = []
        else:
            friendIds = userRow.data[0].get("friends") or []

        # if they have friends we need to look up each one to get their email and display name
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


@ui_bp.route("/user/friends/add", methods=["POST"])
@ui_login_required
def add_friend():
    # get the current user id
    uid = _ui_user()["id"]
    # get the email they typed in the form
    friendEmail = (request.form.get("email") or "").strip().lower()

    if len(friendEmail) == 0:
        return redirect(url_for("ui.manage_friends", status="error", message="Email is required."))

    try:
        calDb = _get_ui_supabase_client()

        # look up the user by email to get their id
        lookup = (
            calDb.table("users")
            .select("id, email")
            .eq("email", friendEmail)
            .execute()
        )

        if len(lookup.data) == 0:
            return redirect(
                url_for("ui.manage_friends", status="error", message=f"No user found with email {friendEmail}")
            )

        friendId = lookup.data[0]["id"]

        # cant add yourself
        if friendId == uid:
            return redirect(
                url_for("ui.manage_friends", status="error", message="You can't add yourself as a friend")
            )

        # get the current friends list so we can check for duplicates
        userRow = calDb.table("users").select("friends").eq("id", uid).execute()
        if len(userRow.data) == 0:
            return redirect(
                url_for("ui.manage_friends", status="error", message=f"User row not found for uid {uid}")
            )

        currentFriends = userRow.data[0].get("friends") or []

        # check if they are already a friend
        alreadyAdded = False
        for fid in currentFriends:
            if str(fid) == str(friendId):
                alreadyAdded = True
                break

        if alreadyAdded == True:
            return redirect(
                url_for("ui.manage_friends", status="error", message=f"{friendEmail} is already in your friends list")
            )

        # add the new friend id to the array
        currentFriends.append(friendId)
        calDb.table("users").update({"friends": currentFriends}).eq("id", uid).execute()

        return redirect(url_for("ui.manage_friends", status="ok", message=f"{friendEmail} added as a friend."))

    except Exception as err:
        return redirect(
            url_for("ui.manage_friends", status="error", message=f"add friend failed for uid {uid}: {err}")
        )


@ui_bp.route("/user/friends/remove", methods=["POST"])
@ui_login_required
def remove_friend():
    # get the current user and the friend id to remove
    uid = _ui_user()["id"]
    friendId = (request.form.get("friend_id") or "").strip()

    if len(friendId) == 0:
        return redirect(url_for("ui.manage_friends", status="error", message="Missing friend id"))

    try:
        calDb = _get_ui_supabase_client()

        # get the current friends list
        userRow = calDb.table("users").select("friends").eq("id", uid).execute()
        if len(userRow.data) == 0:
            return redirect(
                url_for("ui.manage_friends", status="error", message=f"User row not found for uid {uid}")
            )

        currentFriends = userRow.data[0].get("friends") or []

        # build a new list without the friend we want to remove
        newFriends = []
        for fid in currentFriends:
            if str(fid) != str(friendId):
                newFriends.append(fid)

        calDb.table("users").update({"friends": newFriends}).eq("id", uid).execute()

        return redirect(url_for("ui.manage_friends", status="ok", message="Friend removed."))

    except Exception as exc:
        return redirect(
            url_for("ui.manage_friends", status="error", message=f"remove friend failed for uid {uid}: {exc}")
        )

@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    # show the remove account confirmation page
    return render_page("Remove Account", "user", user_nav(), "user/remove_account.html")
