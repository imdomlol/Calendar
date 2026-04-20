# settings page and Google Calendar integration routes (OAuth connect, sync pull, event push, disconnect)
import json
import urllib.error
import urllib.request as urlreq

from flask import redirect, request, session, url_for

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    _google_oauth_config,
    _resolve_app_base_url,
    _ui_user,
    guest_nav,
    render_page,
    ui_login_required,
    user_nav,
)


def _clear_oauth_session():
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)


@ui_bp.route("/settings")
def settings_page():
    user = _ui_user()
    role = "user" if user else "guest"
    nav = user_nav() if user else guest_nav()

    if not user:
        return render_page("Settings", role, nav, "settings/guest.html")

    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    user_id = user.get("id")
    google_rows = []

    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("externals")
            .select("id, provider, url")
            .eq("user_id", user_id)
            .execute()
        )
        all_rows = result.data or []
        google_rows = [
            row
            for row in all_rows
            if "google" in str(row.get("provider") or "").lower()
        ]
    except Exception as exc:
        status = "error"
        message = f"Failed to load external connections: {exc}"

    return render_page(
        "Settings",
        role,
        nav,
        "settings/auth.html",
        status=status,
        message=message,
        google_rows=google_rows,
    )


# --- google OAuth ---
@ui_bp.route("/settings/external/google/connect", methods=["GET", "POST"])
@ui_login_required
def settings_connect_google():
    return redirect(url_for("ui.settings_login_google"))


@ui_bp.route("/settings/external/google/login")
@ui_login_required
def settings_login_google():
    """Starts the Google OAuth2 flow; saves state and redirect URI in session for the callback to verify."""
    client_id, client_secret = _google_oauth_config()

    if not client_id or not client_secret:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=(
                    "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and "
                    "GOOGLE_CLIENT_SECRET in your environment."
                ),
            )
        )

    try:
        from requests_oauthlib import OAuth2Session
    except ImportError as exc:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dependency error: {exc}",
            )
        )

    app_base_url = _resolve_app_base_url()
    redirect_uri = f"{app_base_url}{url_for('ui.settings_google_callback')}"

    oauth = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        scope=[
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
    )
    # offline access_type gets a refresh token; prompt="consent" ensures it is always returned
    authorization_url, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="consent",
    )

    session["google_oauth_state"] = state
    session["google_oauth_redirect_uri"] = redirect_uri
    return redirect(authorization_url)


@ui_bp.route("/settings/external/google/callback")
@ui_login_required
def settings_google_callback():
    """Completes the OAuth2 flow after Google redirects back; upserts the access and refresh tokens in externals."""
    expected_state = (session.get("google_oauth_state") or "").strip()
    returned_state = (request.args.get("state") or "").strip()

    # state param prevents CSRF by matching what we stored in session before the redirect
    if not expected_state or returned_state != expected_state:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="Google OAuth state check failed. Please try again.",
            )
        )

    client_id, client_secret = _google_oauth_config()
    redirect_uri = (session.get("google_oauth_redirect_uri") or "").strip()

    try:
        from requests_oauthlib import OAuth2Session
    except Exception as exc:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dependency error: {exc}",
            )
        )

    if not client_id or not client_secret or not redirect_uri:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="Google OAuth session expired. Please start again.",
            )
        )

    try:
        oauth = OAuth2Session(
            client_id, redirect_uri=redirect_uri, state=expected_state
        )
        credentials = oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=client_secret,
            authorization_response=request.url,
        )

        user_id = _ui_user()["id"]
        provider_url = "https://www.googleapis.com/calendar/v3"
        supabase = _get_ui_supabase_client()

        existing = (
            supabase.table("externals")
            .select("id")
            .eq("user_id", user_id)
            .eq("provider", "google")
            .eq("url", provider_url)
            .execute()
        )

        # upsert: refresh tokens on an existing connection or create a new one
        if existing.data:
            update_payload = {}
            if credentials.get("access_token"):
                update_payload["access_token"] = credentials["access_token"]
            if credentials.get("refresh_token"):
                update_payload["refresh_token"] = credentials["refresh_token"]
            if update_payload:
                supabase.table("externals").update(update_payload).eq(
                    "id", existing.data[0]["id"]
                ).eq("user_id", user_id).execute()
            message = "Google connection refreshed."
        else:
            payload = {"user_id": user_id, "provider": "google", "url": provider_url}
            if credentials.get("access_token"):
                payload["access_token"] = credentials["access_token"]
            if credentials.get("refresh_token"):
                payload["refresh_token"] = credentials["refresh_token"]
            result = supabase.table("externals").insert(payload).execute()
            created_id = (result.data or [{}])[0].get("id") or "new row"
            message = f"Google connection created (id: {created_id})."

        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="ok", message=message))

    except Exception as exc:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"Failed Google OAuth connection: {exc}",
            )
        )


# --- google sync ---
@ui_bp.route("/settings/external/google/<external_id>/sync", methods=["POST"])
@ui_login_required
def settings_sync_google(external_id):
    """Pulls up to 250 events from the user's primary Google Calendar into a local synced calendar."""
    user_id = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()

        ext_result = (
            supabase.table("externals")
            .select("id, access_token")
            .eq("id", external_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not ext_result.data:
            return redirect(
                url_for(
                    "ui.settings_page", status="error", message="Connection not found."
                )
            )

        access_token = ext_result.data.get("access_token")
        if not access_token:
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="error",
                    message="No access token stored. Please reconnect Google.",
                )
            )

        api_url = (
            "https://www.googleapis.com/calendar/v3/calendars/primary/events"
            "?maxResults=250&orderBy=startTime&singleEvents=true"
        )
        req = urlreq.Request(
            api_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        try:
            with urlreq.urlopen(req) as resp:
                google_events = json.loads(resp.read().decode("utf-8")).get("items", [])
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                return redirect(
                    url_for(
                        "ui.settings_page",
                        status="error",
                        message="Google access token expired. Please reconnect Google to refresh it.",
                    )
                )
            raise

        cal_result = (
            supabase.table("calendars")
            .select("id")
            .eq("owner_id", user_id)
            .eq("name", "Google Calendar (Synced)")
            .execute()
        )
        # find or create the dedicated import calendar so synced events stay separate from local ones
        if cal_result.data:
            calendar_id = str(cal_result.data[0]["id"])
        else:
            new_cal = (
                supabase.table("calendars")
                .insert(
                    {
                        "name": "Google Calendar (Synced)",
                        "owner_id": user_id,
                        "member_ids": [user_id],
                        "events": [],
                    }
                )
                .execute()
            )
            calendar_id = str(new_cal.data[0]["id"])

        payloads = []
        for g_event in google_events:
            start = g_event.get("start", {})
            end = g_event.get("end", {})
            payload = {
                "title": g_event.get("summary") or "Untitled Event",
                "calendar_ids": [calendar_id],
                "owner_id": user_id,
                "start_timestamp": start.get("dateTime") or start.get("date"),
                "end_timestamp": end.get("dateTime") or end.get("date"),
            }
            if g_event.get("description"):
                payload["description"] = g_event["description"]
            payloads.append(payload)

        if payloads:
            supabase.table("events").insert(payloads).execute()
        inserted = len(payloads)

        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pulled {inserted} events into 'Google Calendar (Synced)'.",
            )
        )

    except Exception as exc:
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Sync failed: {exc}")
        )


@ui_bp.route("/settings/external/google/<external_id>/push", methods=["POST"])
@ui_login_required
def settings_push_google(external_id):
    """Pushes all local non-synced events to the user's primary Google Calendar one at a time."""
    user_id = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()

        ext_result = (
            supabase.table("externals")
            .select("id, access_token")
            .eq("id", external_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not ext_result.data:
            return redirect(
                url_for(
                    "ui.settings_page", status="error", message="Connection not found."
                )
            )

        access_token = ext_result.data.get("access_token")
        if not access_token:
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="error",
                    message="No access token stored. Please reconnect Google.",
                )
            )

        # excludes the "Google Calendar (Synced)" import calendar to avoid pushing synced events back
        cals_result = (
            supabase.table("calendars")
            .select("id")
            .eq("owner_id", user_id)
            .neq("name", "Google Calendar (Synced)")
            .execute()
        )
        calendar_ids = [str(c["id"]) for c in (cals_result.data or [])]

        if not calendar_ids:
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="ok",
                    message="No local calendars to push.",
                )
            )

        events_result = (
            supabase.table("events")
            .select("title, description, start_timestamp, end_timestamp")
            .overlaps("calendar_ids", calendar_ids)
            .execute()
        )
        local_events = events_result.data or []

        if not local_events:
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="ok",
                    message="No local events found to push.",
                )
            )

        # fetch the primary calendar timezone so events land at the correct local time on Google's end
        cal_tz = "UTC"
        try:
            tz_req = urlreq.Request(
                "https://www.googleapis.com/calendar/v3/calendars/primary",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            with urlreq.urlopen(tz_req) as tz_resp:
                cal_tz = json.loads(tz_resp.read().decode("utf-8")).get(
                    "timeZone", "UTC"
                )
        except Exception:
            pass  # fall back to UTC if the lookup fails

        # converts a stored timestamp to a Google Calendar time object with the correct timezone applied
        def _as_time_obj(ts):
            ts = str(ts)
            if "T" in ts or len(ts) > 10:
                # timestamps are local time that PostgreSQL tagged as +00:00; strip the offset so Google
                # applies the calendar timezone instead of treating the value as UTC
                clean_ts = ts.replace("+00:00", "").replace("Z", "")
                return {"dateTime": clean_ts, "timeZone": cal_tz}
            return {"date": ts}

        api_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # TODO: pushing one event per request is slow; Google Calendar batch API would help here
        pushed = 0
        for event in local_events:
            start_ts = event.get("start_timestamp")
            if not start_ts:
                continue  # Google Calendar requires a start time

            end_ts = event.get("end_timestamp") or start_ts
            body = {
                "summary": event.get("title") or "Untitled Event",
                "start": _as_time_obj(start_ts),
                "end": _as_time_obj(end_ts),
            }
            if event.get("description"):
                body["description"] = event["description"]

            req = urlreq.Request(
                api_url,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with urlreq.urlopen(req) as resp:
                    resp.read()
                pushed += 1
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    return redirect(
                        url_for(
                            "ui.settings_page",
                            status="error",
                            message=(
                                "Google denied write access. "
                                "Please disconnect and reconnect Google to grant calendar write permission."
                            ),
                        )
                    )
                raise

        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pushed {pushed} events to Google Calendar.",
            )
        )

    except Exception as exc:
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Push failed: {exc}")
        )


# --- disconnect ---
@ui_bp.route("/settings/external/google/<external_id>/disconnect", methods=["POST"])
@ui_login_required
def settings_disconnect_google(external_id):
    user_id = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()
        existing = (
            supabase.table("externals")
            .select("id, provider")
            .eq("id", external_id)
            .eq("user_id", user_id)
            .execute()
        )

        rows = existing.data or []
        if not rows:
            return redirect(
                url_for(
                    "ui.settings_page", status="error", message="Connection not found."
                )
            )

        if "google" not in str(rows[0].get("provider") or "").lower():
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="error",
                    message="Only Google connections can be removed from this section.",
                )
            )

        supabase.table("externals").delete().eq("id", external_id).eq(
            "user_id", user_id
        ).execute()
        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message="Google connection disconnected.",
            )
        )

    except Exception as exc:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"Failed to disconnect Google connection: {exc}",
            )
        )
