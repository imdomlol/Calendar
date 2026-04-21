import json
import urllib.request as urlreq
from flask import redirect, request, session, url_for
import urllib.error

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _get_ui_supabase_client,
    _google_oauth_config,
    render_page,
    ui_login_required,
)
from api.ui_routes.helpers import _resolve_app_base_url, _ui_user, guest_nav, user_nav


def _clear_oauth_session():
    # this function removes the google oauth stuff from the session
    # we call it when oauth finishes or when something goes wrong
    # it cleans up so there is no leftover data in the session
    # first we remove the state value
    # the state is a random string we use to check that nothing tampered with the flow
    session.pop("google_oauth_state", None)
    # now remove the redirect uri we saved earlier
    # the redirect uri is the url we told google to send the user back to
    # we stored it in the session before starting oauth so we clean it up here
    session.pop("google_oauth_redirect_uri", None)
    # the function doesnt return anything it just removes stuff


@ui_bp.route("/settings")
def settings_page():
    # get the current user from the session
    user = _ui_user()
    # check if user is logged in to figure out the role
    if user:
        role = "user"
    else:
        role = "guest"
    nav = user_nav() if user else guest_nav()

    if not user:
        return render_page("Settings", role, nav, "settings/guest.html")

    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    userId = user.get("id")
    google_rows = []

    try:
        supabase = _get_ui_supabase_client()
        result = (
            supabase.table("externals")
            .select("id, provider, url")
            .eq("user_id", userId)
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

@ui_bp.route("/settings/external/google/connect", methods=["GET", "POST"])
@ui_login_required
def settings_connect_google():
    return redirect(url_for("ui.settings_login_google"))



@ui_bp.route("/settings/external/google/login")
@ui_login_required
def settings_login_google():
    clientId, client_secret = _google_oauth_config()

    if not clientId or not client_secret:
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

    appBaseUrl = _resolve_app_base_url()
    redirect_uri = f"{appBaseUrl}{url_for('ui.settings_google_callback')}"

    oauth = OAuth2Session(
        clientId,
        redirect_uri=redirect_uri,
        scope=[
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
    )

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
    exp_state = (session.get("google_oauth_state") or "").strip()
    ret_state = (request.args.get("state") or "").strip()

    # check the state matches what we stored before the oauth redirect
    if not exp_state or ret_state != exp_state:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="Google OAuth state check failed. Please try again.",
            )
        )

    clientId, client_secret = _google_oauth_config()
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

    if not clientId or not client_secret or not redirect_uri:
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
            clientId, redirect_uri=redirect_uri, state=exp_state
        )
        creds = oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=client_secret,
            authorization_response=request.url,
        )

        uid = _ui_user()["id"]
        provider_url = "https://www.googleapis.com/calendar/v3"
        supabase = _get_ui_supabase_client()

        existing = (
            supabase.table("externals")
            .select("id")
            .eq("user_id", uid)
            .eq("provider", "google")
            .eq("url", provider_url)
            .execute()
        )

        # upsert: update tokens if connection exists or create a new one
        if existing.data:
            updateData = {}
            if creds.get("access_token"):
                updateData["access_token"] = creds["access_token"]
            if creds.get("refresh_token"):
                updateData["refresh_token"] = creds["refresh_token"]
            if updateData:
                supabase.table("externals").update(updateData).eq(
                    "id", existing.data[0]["id"]
                ).eq("user_id", uid).execute()
            message = "Google connection refreshed."
        else:
            payload = {"user_id": uid, "provider": "google", "url": provider_url}
            if creds.get("access_token"):
                payload["access_token"] = creds["access_token"]
            if creds.get("refresh_token"):
                payload["refresh_token"] = creds["refresh_token"]
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




@ui_bp.route("/settings/external/google/<external_id>/sync", methods=["POST"])
@ui_login_required
def settings_sync_google(external_id):
    uid = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()

        ext_result = (
            supabase.table("externals")
            .select("id, access_token")
            .eq("id", external_id)
            .eq("user_id", uid)
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
                gEvents = json.loads(resp.read().decode("utf-8")).get("items", [])
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
            .eq("owner_id", uid)
            .eq("name", "Google Calendar (Synced)")
            .execute()
        )
        # find or create the import calendar so synced events stay separate
        if cal_result.data:
            calendar_id = str(cal_result.data[0]["id"])
        else:
            new_cal = (
                supabase.table("calendars")
                .insert(
                    {
                        "name": "Google Calendar (Synced)",
                        "owner_id": uid,
                        "member_ids": [uid],
                        "events": [],
                    }
                )
                .execute()
            )
            calendar_id = str(new_cal.data[0]["id"])

        payloads = []
        for i in range(0, len(gEvents)):
            g_event = gEvents[i]
            start = g_event.get("start", {})
            end = g_event.get("end", {})
            payload = {
                "title": g_event.get("summary") or "Untitled Event",
                "calendar_ids": [calendar_id],
                "owner_id": uid,
                "start_timestamp": start.get("dateTime") or start.get("date"),
                "end_timestamp": end.get("dateTime") or end.get("date"),
            }
            if g_event.get("description"):
                payload["description"] = g_event["description"]
            payloads.append(payload)

        if len(payloads) > 0:
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
    uid = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()

        ext_result = (
            supabase.table("externals")
            .select("id, access_token")
            .eq("id", external_id)
            .eq("user_id", uid)
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

        # skip the synced import calendar to avoid pushing those events back
        cals_result = (
            supabase.table("calendars")
            .select("id")
            .eq("owner_id", uid)
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
            pass

        def _as_time_obj(ts):
            ts = str(ts)
            if "T" in ts or len(ts) > 10:
                clean_ts = ts.replace("+00:00", "").replace("Z", "")
                return {"dateTime": clean_ts, "timeZone": cal_tz}
            return {"date": ts}

        api_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        pushed = 0
        for event in local_events:
            startTs = event.get("start_timestamp")
            if not startTs:
                continue

            end_ts = event.get("end_timestamp") or startTs
            body = {
                "summary": event.get("title") or "Untitled Event",
                "start": _as_time_obj(startTs),
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


@ui_bp.route("/settings/external/google/<external_id>/disconnect", methods=["POST"])
@ui_login_required
def settings_disconnect_google(external_id):
    uid = _ui_user()["id"]

    try:
        supabase = _get_ui_supabase_client()
        existing = (
            supabase.table("externals")
            .select("id, provider")
            .eq("id", external_id)
            .eq("user_id", uid)
            .execute()
        )

        rows = existing.data or []
        if len(rows) == 0:
            return redirect(
                url_for(
                    "ui.settings_page", status="error", message="Connection not found."
                )
            )

        provName = str(rows[0].get("provider") or "").lower()
        isGoogle = "google" in provName
        if isGoogle == False:
            return redirect(
                url_for(
                    "ui.settings_page",
                    status="error",
                    message="Only Google connections can be removed from this section.",
                )
            )

        supabase.table("externals").delete().eq("id", external_id).eq(
            "user_id", uid
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
