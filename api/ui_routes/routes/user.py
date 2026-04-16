from html import escape

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
    items = "".join(f"<li>{name}</li>" for name in placeholder_externals)
    body = f"""
    <div class='hero'><h1>Manage Externals</h1><p class='muted'>Connect, disconnect, sync now, or toggle auto-sync.</p></div>
    <div class='grid'>
      <div class='card'><h4>Connected providers</h4><ul>{items}</ul></div>
      <div class='card'><h4>Actions</h4><p>Connect external calendar</p><p>Disconnect external calendar</p><p>Sync now</p><p>Enable/Disable auto sync</p></div>
    </div>
    """
    return render_page("Manage Externals", "user", user_nav(), body)


@ui_bp.route("/user/calendars")
@ui_login_required
def manage_calendars():
    owner_id = _ui_user()["id"]
    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()

    records = []
    if owner_id:
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

    cards = []
    for cal in records:
        calendar_id = escape(str(cal.get("id") or ""))
        calendar_name = escape(str(cal.get("name") or "Untitled"))
        calendar_owner = escape(str(cal.get("owner_id") or ""))
        member_list = cal.get("member_ids") or []
        members = "".join(f"<li>{escape(str(m))}</li>" for m in member_list) or "<li>No members yet</li>"
        event_count = len(cal.get("events") or [])
        cards.append(f"""
          <div class='card'>
            <div class='pill'>Calendar #{calendar_id}</div>
            <h4>{calendar_name}</h4>
            <p>Owner ID: {calendar_owner}</p>
            <p>Events linked: {event_count}</p>
            <p><strong>Actions:</strong> Create event, edit event, delete event, manage members, remove calendar</p>
            <ul>{members}</ul>
          </div>
        """)

    banner = ""
    if message:
        banner_class = "#dcfce7" if status == "ok" else "#fee2e2"
        border_class = "#86efac" if status == "ok" else "#fca5a5"
        banner = f"<div class='card' style='margin-bottom:16px; background:{banner_class}; border-color:{border_class};'><p>{escape(message)}</p></div>"

    results_section = (
        "<div class='grid'>" + "".join(cards) + "</div>"
        if cards
        else "<div class='empty'><h3>No calendars found</h3><p>No calendar rows exist for this owner id yet.</p></div>"
    )

    safe_owner_value = escape(owner_id)
    body = """
    <div class='hero'>
      <h1>Manage Calendars</h1>
      <p class='muted'>Create calendars in Supabase. Owner id is auto-filled from your login.</p>
    </div>
    """ + banner + """
    <div class='card' style='margin-bottom:16px;'>
      <h4>Available actions</h4>
      <p>Create Calendar • Add Member • Remove Member • Manage Events • Remove Calendar</p>
      <p class='muted'>Logged in as owner id: """ + safe_owner_value + """</p>
      <form method='POST' action='/ui/user/calendars/create' style='margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;'>
        <input type='hidden' name='owner_id' value='""" + safe_owner_value + """' />
        <input type='text' name='name' placeholder='Calendar name (required)' required
          style='padding:10px; border:1px solid #cbd5e1; border-radius:10px; min-width:220px;' />
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0;'>Create Calendar</button>
      </form>
    </div>
    """ + results_section
    return render_page("Manage Calendars", "user", user_nav(), body)


@ui_bp.route("/user/calendars/create", methods=["POST"])
@ui_login_required
def create_calendar():
    name = (request.form.get("name") or "").strip()
    owner_id = _ui_user()["id"]

    if not owner_id or not name:
        return redirect(url_for(
            "ui.manage_calendars",
            owner_id=owner_id,
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
            owner_id=owner_id,
            status="ok",
            message=f"Calendar created successfully (id: {created_id}).",
        ))
    except Exception as exc:
        return redirect(url_for(
            "ui.manage_calendars",
            owner_id=owner_id,
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
    events_rows = []

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
            if not selected_calendar_id or not any(str(c.get("id")) == selected_calendar_id for c in calendars):
                selected_calendar_id = str(calendars[0].get("id"))

            events_result = (
                supabase.table("events")
                .select("id, title, description, start_timestamp, end_timestamp")
                .overlaps("calendar_ids", [selected_calendar_id])
                .order("start_timestamp", desc=False)
                .execute()
            )
            events_rows = events_result.data or []
    except Exception as exc:
        status = "error"
        message = f"Failed to load events: {exc}"

    banner = ""
    if message:
        banner_bg = "#dcfce7" if status == "ok" else "#fee2e2"
        banner_border = "#86efac" if status == "ok" else "#fca5a5"
        banner = (
            f"<div class='card' style='margin-bottom:16px; background:{banner_bg}; border-color:{banner_border};'>"
            f"<p>{escape(message)}</p></div>"
        )

    if not calendars:
        body = """
        <div class='hero'>
          <h1>Manage Events</h1>
          <p class='muted'>Create events by attaching them to one of your calendars.</p>
        </div>
        """ + banner + """
        <div class='card'>
          <h4>No calendars available</h4>
          <p>Create a calendar first, then come back to add events.</p>
          <a class='btn' href='/ui/user/calendars'>Go to Calendars</a>
        </div>
        """
        return render_page("Manage Events", "user", user_nav(), body)

    calendar_options = "".join(
        (
            f"<option value='{escape(str(c.get('id')))}'"
            + (" selected" if str(c.get("id")) == selected_calendar_id else "")
            + f">{escape(str(c.get('name') or 'Untitled Calendar'))}</option>"
        )
        for c in calendars
    )

    event_rows_html = "".join(
        "<tr>"
        f"<td>{escape(str(event.get('title') or 'Untitled'))}</td>"
        f"<td>{escape(str(event.get('start_timestamp') or ''))}</td>"
        f"<td>{escape(str(event.get('end_timestamp') or ''))}</td>"
        "</tr>"
        for event in events_rows
    ) or "<tr><td colspan='3' class='muted'>No events found for this calendar.</td></tr>"

    body = """
    <div class='hero'>
      <h1>Manage Events</h1>
      <p class='muted'>Create an event and attach it to one of your calendars.</p>
    </div>
    """ + banner + """
    <div class='card' style='margin-bottom:16px;'>
      <form method='GET' action='/ui/user/events' style='display:flex; gap:8px; align-items:center; flex-wrap:wrap;'>
        <label for='calendar_id'><strong>View calendar:</strong></label>
        <select id='calendar_id' name='calendar_id' style='padding:8px; border:1px solid #cbd5e1; border-radius:8px; min-width:240px;'>
          """ + calendar_options + """
        </select>
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0;'>Load</button>
      </form>
    </div>
    <div class='card' style='margin-bottom:16px;'>
      <h4>Add Event</h4>
      <form method='POST' action='/ui/user/events/create' style='display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:10px;'>
        <select name='calendar_id' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;'>
          """ + calendar_options + """
        </select>
        <input type='text' name='title' placeholder='Event title' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='datetime-local' name='start_timestamp' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='datetime-local' name='end_timestamp' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
        <input type='text' name='description' placeholder='Description (optional)' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px; grid-column:1/-1;' />
        <button type='submit' class='btn' style='border:none; cursor:pointer; margin-top:0; width:max-content;'>Create Event</button>
      </form>
    </div>
    <div class='card'>
      <h4>Events in selected calendar</h4>
      <table>
        <tr><th>Title</th><th>Start</th><th>End</th></tr>
        """ + event_rows_html + """
      </table>
    </div>
    """
    return render_page("Manage Events", "user", user_nav(), body)


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
    names = "".join(f"<li>{friend}</li>" for friend in placeholder_friends)
    body = f"""
    <div class='hero'><h1>Manage Friends</h1><p class='muted'>Add and remove friends.</p></div>
    <div class='grid'>
      <div class='card'><h4>Friends List</h4><ul>{names}</ul></div>
      <div class='card'><h4>Actions</h4><p>Add Friend</p><p>Remove Friend</p></div>
    </div>
    """
    return render_page("Manage Friends", "user", user_nav(), body)


@ui_bp.route("/user/remove-account")
@ui_login_required
def remove_account():
    body = """
    <div class='hero'><h1>Remove Account</h1><p class='muted'>This is a placeholder confirmation screen.</p></div>
    <div class='card'>
      <h4>Danger Zone</h4>
      <p>This action would permanently remove the user's account.</p>
      <a class='btn danger' href='/ui/dashboard/user'>Confirm removal</a>
    </div>
    """
    return render_page("Remove Account", "user", user_nav(), body)
