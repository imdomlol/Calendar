import secrets
from datetime import datetime, timedelta

from flask import jsonify, redirect, request, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _make_ui_user,
    _resolve_app_base_url,
    _ui_user,
    render_page,
    resolve_member_id,
    ui_login_required,
)
from models.calendar import Calendar
from models.event import Event
from models.external import External
from utils.supabase_client import get_supabase_client


# ========================= Page Routes =========================


@ui_bp.route("/user/externals")
@ui_login_required
def manage_externals():
    # show the connected external accounts page
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    providersList = []

    try:
        # load this users connected providers
        uiUser = _make_ui_user()
        providersList = uiUser.listExternals()
    except Exception as error:
        status = "error"
        message = f"Couldn't load external connections: {error}"

    return render_page(
        "Manage Externals",
        "user/externals.html",
        providers=providersList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    # show the page for calendars owned by the user
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    records = []

    try:
        # ask the model for calendars attached to this account
        uiUser = _make_ui_user()
        records = uiUser.listCalendars()
    except Exception as error:
        status = "error"
        message = f"Couldn't load calendars: {error}"

    return render_page(
        "Manage Calendars",
        "user/calendars.html",
        status=status,
        message=message,
        owner_id=_ui_user()["id"],
        calendars=records,
        has_guest_link_fields=True,
        app_base_url=_resolve_app_base_url(),
    )


@ui_bp.route("/user/events")
@ui_login_required
def manage_events():
    # show events for the selected calendar
    selectedCalendarId = (request.args.get("calendar_id") or "").strip()
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    calendars = []
    events = []

    try:
        uiUser = _make_ui_user()
        calendars = uiUser.listCalendars()

        if calendars:
            selectedCalendar = calendars[0]

            # look for the calendar requested in the query string
            for calendar in calendars:
                calendarId = str(calendar.get("id"))
                if calendarId == selectedCalendarId:
                    selectedCalendar = calendar
                    break

            selectedCalendarId = str(selectedCalendar.get("id"))
            events = Calendar.list_events(selectedCalendarId)
    except Exception as error:
        status = "error"
        message = f"Couldn't load events: {error}"

    if not calendars:
        return render_page(
            "Manage Events",
            "user/events_no_calendars.html",
            status=status,
            message=message,
        )

    # build default form times for a one hour event
    now = datetime.now()
    defaultStart = now.strftime("%Y-%m-%dT%H:%M")
    defaultEnd = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")

    return render_page(
        "Manage Events",
        "user/events.html",
        status=status,
        message=message,
        calendars=calendars,
        selected_calendar_id=selectedCalendarId,
        events=events,
        default_start=defaultStart,
        default_end=defaultEnd,
    )


@ui_bp.route("/user/events/<event_id>/edit")
@ui_login_required
def edit_event(event_id):
    # show the edit page when the event belongs to the user
    userId = _ui_user()["id"]
    event = Event.find(event_id)

    if not event or event.get("owner_id") != userId:
        return redirect(
            url_for(
                "ui.manage_events",
                status="error",
                message=f"Event {event_id} not found",
            )
        )

    return render_page(
        "Edit Event",
        "user/events_edit.html",
        event=event,
        status="",
        message="",
    )


@ui_bp.route("/user/friends")
@ui_login_required
def manage_friends():
    # show the friends page with friend data
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    friendsList = []

    try:
        uiUser = _make_ui_user()
        friendsList = uiUser.listFriendsData()
    except Exception as error:
        status = "error"
        message = f"Couldn't load friends: {error}"

    return render_page(
        "Manage Friends",
        "user/friends.html",
        friends=friendsList,
        status=status,
        message=message,
    )


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    # show the remove account page
    return render_page("Remove Account", "user/remove_account.html")


# ========================= Event API Routes =========================


@ui_bp.route("/user/events", methods=["POST"])
@ui_login_required
def create_event():
    # create an event for one or more calendars
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    calendarIds = []

    # keep only real calendar ids from the posted JSON
    for calendarId in body.get("calendar_ids") or []:
        if calendarId:
            calendarIds.append(str(calendarId))

    if not title or not calendarIds:
        return jsonify({"error": "title and calendar_ids are required"}), 400

    user = _make_ui_user()
    userCalIds = []

    # collect the calendar ids the user is allowed to write to
    for calendar in user.listCalendars():
        userCalIds.append(str(calendar["id"]))

    hasAllowedCalendar = False
    for calendarId in calendarIds:
        if calendarId in userCalIds:
            hasAllowedCalendar = True
            break

    if not hasAllowedCalendar:
        return jsonify({"error": "not authorized for any of the given calendars"}), 403

    event = Event(
        title=title,
        calendarIds=calendarIds,
        ownerId=user.userId,
        description=body.get("description"),
        startTimestamp=body.get("start_timestamp"),
        endTimestamp=body.get("end_timestamp"),
    )
    result = event.save()
    rows = result.data or []

    if rows:
        return jsonify(rows[0]), 201

    return jsonify(event.to_record()), 201


@ui_bp.route("/user/events/<event_id>", methods=["PUT"])
@ui_login_required
def update_event(event_id):
    # update a users event after checking calendar access
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()

    if not result.data:
        return jsonify({"error": "event not found"}), 404

    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = []

    for calendar in user.listCalendars():
        userCalIds.append(calendar["id"])

    canEditEvent = False
    for calendarId in eventData.get("calendar_ids", []):
        if calendarId in userCalIds:
            canEditEvent = True
            break

    if not canEditEvent:
        return jsonify({"error": "not authorized to edit this event"}), 403

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    description = body.get("description")
    startTimestamp = body.get("start_timestamp")
    endTimestamp = body.get("end_timestamp")
    calendarIds = body.get("calendar_ids")
    updateValues = [title, description, startTimestamp, endTimestamp, calendarIds]
    hasUpdateValue = False

    # check if the request actually sent something to update
    for value in updateValues:
        if value is not None:
            hasUpdateValue = True
            break

    if not hasUpdateValue:
        return jsonify({"error": "no fields to update"}), 400

    event = Event(
        title=eventData["title"],
        calendarIds=eventData["calendar_ids"],
        ownerId=eventData["owner_id"],
    )
    event.id = event_id
    editResult = event.edit(
        title=title,
        description=description,
        startTimestamp=startTimestamp,
        endTimestamp=endTimestamp,
        calendarIds=calendarIds,
    )

    return jsonify(editResult.data[0]), 200


@ui_bp.route("/user/events/<event_id>", methods=["DELETE"])
@ui_login_required
def delete_event(event_id):
    # delete an event only when the user belongs to one of its calendars
    db = get_supabase_client()
    result = db.table("events").select("*").eq("id", event_id).execute()

    if not result.data:
        return jsonify({"error": "event not found"}), 404

    eventData = result.data[0]
    user = _make_ui_user()
    userCalIds = []

    for calendar in user.listCalendars():
        userCalIds.append(calendar["id"])

    canDeleteEvent = False
    for calendarId in eventData.get("calendar_ids", []):
        if calendarId in userCalIds:
            canDeleteEvent = True
            break

    if not canDeleteEvent:
        return jsonify({"error": "not authorized to delete this event"}), 403

    event = Event(
        title=eventData["title"],
        calendarIds=eventData["calendar_ids"],
    )
    event.id = event_id
    event.remove()

    return "", 204


# ========================= Calendar API Routes =========================


@ui_bp.route("/user/calendars", methods=["POST"])
@ui_login_required
def create_calendar():
    # make a new calendar owned by the current user
    body = request.get_json(silent=True) or {}
    name = body.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    userId = _ui_user()["id"]
    calendar = Calendar(name=name, ownerId=userId)
    result = calendar.save()

    return jsonify(result.data[0]), 201


@ui_bp.route("/user/calendars/<calendar_id>", methods=["DELETE"])
@ui_login_required
def delete_calendar(calendar_id):
    # remove a calendar if the current user owns it
    db = get_supabase_client()
    userId = _ui_user()["id"]
    existing = (
        db.table("calendars")
        .select("id", "name", "owner_id")
        .eq("id", calendar_id)
        .eq("owner_id", userId)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404

    calData = existing.data[0]
    calendar = Calendar(
        name=calData["name"],
        ownerId=calData["owner_id"],
    )
    calendar.id = calendar_id
    calendar.remove()

    return "", 204


@ui_bp.route("/user/calendars/<calendar_id>/members/me", methods=["DELETE"])
@ui_login_required
def leave_calendar(calendar_id):
    # remove the current user from a shared calendar
    db = get_supabase_client()
    userId = str(_ui_user()["id"])
    existing = (
        db.table("calendars")
        .select("id, name, owner_id, member_ids")
        .eq("id", calendar_id)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found"}), 404

    calData = existing.data[0]
    ownerId = str(calData["owner_id"])

    if ownerId == userId:
        return jsonify({"error": "calendar owners cannot remove themselves"}), 400

    memberIds = []
    for memberId in calData.get("member_ids") or []:
        memberIds.append(str(memberId))

    if userId not in memberIds:
        return jsonify({"error": "you are not a member of this calendar"}), 403

    calendar = Calendar(
        name=calData["name"],
        ownerId=ownerId,
    )
    calendar.id = calendar_id
    calendar.memberIds = memberIds
    result = calendar.remove_member(userId)

    if not result.data:
        return jsonify({"error": "calendar membership was not updated"}), 500

    return "", 204


@ui_bp.route("/calendars/<calendar_id>/members/<member_id>", methods=["DELETE"])
@ui_login_required
def remove_calendar_member(calendar_id, member_id):
    # let the owner remove another member from a calendar
    db = get_supabase_client()
    userId = _ui_user()["id"]
    existing = (
        db.table("calendars")
        .select("id, name, owner_id, member_ids")
        .eq("id", calendar_id)
        .eq("owner_id", userId)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404

    calData = existing.data[0]

    if member_id == calData["owner_id"]:
        return jsonify({"error": "calendar owners cannot remove themselves"}), 400

    existingMemberIds = []
    fallbackMemberIds = calData.get("member_ids") or [calData["owner_id"]]
    for existingMemberId in fallbackMemberIds:
        existingMemberIds.append(str(existingMemberId))

    calendar = Calendar(
        name=calData["name"],
        ownerId=calData["owner_id"],
    )
    calendar.id = calendar_id
    calendar.memberIds = existingMemberIds

    try:
        result = calendar.remove_member(str(member_id))
    except KeyError as error:
        return jsonify({"error": str(error)}), 404
    except (ValueError, Exception) as error:
        return jsonify({"error": str(error)}), 400

    if not result.data:
        return jsonify({"error": "calendar membership was not updated"}), 500

    return "", 204


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["POST"])
@ui_login_required
def create_guest_link(calendar_id):
    # create a share link for a calendar the user owns
    db = get_supabase_client()
    userId = _ui_user()["id"]
    existing = (
        db.table("calendars")
        .select("id")
        .eq("id", calendar_id)
        .eq("owner_id", userId)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404

    body = request.get_json(silent=True) or {}
    role = body.get("role", "viewer")

    if role not in ("viewer", "editor"):
        return jsonify({"error": "role must be viewer or editor"}), 400

    token = secrets.token_urlsafe(32)
    result = (
        db.table("calendars")
        .update(
            {
                "guest_link_token": token,
                "guest_link_role": role,
                "guest_link_active": True,
            }
        )
        .eq("id", calendar_id)
        .execute()
    )

    return jsonify(result.data[0]), 200


@ui_bp.route("/user/calendars/<calendar_id>/guest-link", methods=["DELETE"])
@ui_login_required
def revoke_guest_link(calendar_id):
    # turn off the guest link for a calendar
    db = get_supabase_client()
    userId = _ui_user()["id"]
    existing = (
        db.table("calendars")
        .select("id")
        .eq("id", calendar_id)
        .eq("owner_id", userId)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404

    db.table("calendars").update(
        {
            "guest_link_token": None,
            "guest_link_role": None,
            "guest_link_active": False,
        }
    ).eq("id", calendar_id).execute()

    return "", 204


@ui_bp.route("/calendars/<calendar_id>/members", methods=["POST"])
@ui_login_required
def add_calendar_member(calendar_id):
    # add another app user to a calendar
    db = get_supabase_client()
    userId = _ui_user()["id"]
    existing = (
        db.table("calendars")
        .select("id, name, owner_id, member_ids")
        .eq("id", calendar_id)
        .eq("owner_id", userId)
        .execute()
    )

    if not existing.data:
        return jsonify({"error": "calendar not found or not owned by you"}), 404

    body = request.get_json(silent=True) or {}
    value = (body.get("member") or "").strip()

    if not value:
        return jsonify({"error": "member is required"}), 400

    memberId = resolve_member_id(value)
    if not memberId:
        return jsonify({"error": "no user found with that email"}), 404

    calData = existing.data[0]
    calendar = Calendar(
        name=calData["name"],
        ownerId=calData["owner_id"],
    )
    calendar.id = calendar_id
    calendar.memberIds = calData.get("member_ids") or [calData["owner_id"]]

    try:
        calendar.add_member(memberId)
    except (ValueError, Exception) as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"ok": True}), 200


# ========================= Friend API Routes =========================


@ui_bp.route("/user/friends", methods=["POST"])
@ui_login_required
def add_friend():
    # add a friend by id email or input value
    body = request.get_json(silent=True) or {}
    user = _make_ui_user()

    try:
        friends = user.addFriend(
            friendId=body.get("friend_id"),
            email=body.get("email"),
            value=body.get("value"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"friends": friends})


@ui_bp.route("/user/friends/<friend_id>", methods=["DELETE"])
@ui_login_required
def remove_friend(friend_id):
    # remove one friend from the current user
    user = _make_ui_user()

    try:
        user.removeFriend(friend_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 404

    return "", 204


# ========================= Account API Routes =========================


@ui_bp.route("/user/me", methods=["DELETE"])
@ui_login_required
def delete_me():
    # delete the current users account
    user = _make_ui_user()
    user.removeAccount()

    return "", 204


@ui_bp.route("/settings/external/<external_id>", methods=["DELETE"])
@ui_login_required
def disconnect_external(external_id):
    # disconnect one external provider from settings
    userId = _ui_user()["id"]
    db = get_supabase_client()
    external = External(
        id=external_id,
        supabaseClient=db,
        userId=userId,
    )

    try:
        external.remove(external_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 404

    return "", 204
