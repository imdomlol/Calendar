from flask import redirect, request, session, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    _google_oauth_config,
    _resolve_app_base_url,
    render_page,
    ui_login_required,
    guest_nav,
    user_nav,
)
from models.external import External
from utils.supabase_client import get_supabase_client


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
    google_rows = []
    try:
        u = _make_ui_user()
        all_externals = u.listExternals()
        google_rows = [e for e in all_externals if "google" in str(e.get("provider") or "").lower()]
    except Exception as e:
        status = "error"
        message = f"Couldn't load externals: {e}"

    return render_page(
        "Settings", role, nav, "settings/auth.html",
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
        return redirect(url_for("ui.settings_page", status="error",
                                message="Google OAuth not configured, set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"))

    try:
        from requests_oauthlib import OAuth2Session
    except ImportError as e:
        return redirect(url_for("ui.settings_page", status="error", message=f"OAuth dep missing: {e}"))

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
    if not exp_state or ret_state != exp_state:
        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message="OAuth state mismatch"))

    clientId, client_secret = _google_oauth_config()
    redirect_uri = (session.get("google_oauth_redirect_uri") or "").strip()

    try:
        from requests_oauthlib import OAuth2Session
    except Exception as err:
        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message=f"OAuth dep missing: {err}"))

    if not clientId or not client_secret or not redirect_uri:
        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="error",
                                message="OAuth session expired, missing clientId or redirect_uri"))

    try:
        oauth = OAuth2Session(clientId, redirect_uri=redirect_uri, state=exp_state)
        creds = oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=client_secret,
            authorization_response=request.url,
        )

        uid = _ui_user()["id"]
        provider_url = "https://www.googleapis.com/calendar/v3"
        u = _make_ui_user()
        existing = next(
            (e for e in u.listExternals()
             if e.get("provider") == "google" and e.get("url") == provider_url),
            None,
        )

        db = get_supabase_client()
        if existing:
            ext = External(id=existing["id"], url=provider_url, provider="google",
                           supabaseClient=db, userId=uid)
            ext.updateTokens(existing["id"], uid,
                             accessToken=creds.get("access_token"),
                             refreshToken=creds.get("refresh_token"))
            message = "Google connection refreshed."
        else:
            ext = External(id=None, url=provider_url, provider="google",
                           supabaseClient=db, userId=uid,
                           accessToken=creds.get("access_token"),
                           refreshToken=creds.get("refresh_token"))
            result = ext.save()
            created_id = (result.data or [{}])[0].get("id") or "new row"
            message = f"Google connection created (id: {created_id})."

        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="ok", message=message))

    except Exception as exc:
        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message=f"Google OAuth failed: {exc}"))


@ui_bp.route("/settings/external/google/<external_id>/sync", methods=["POST"])
@ui_login_required
def settings_sync_google(external_id):
    uid = _ui_user()["id"]
    try:
        db = get_supabase_client()
        ext = External(id=external_id, url="", provider="", supabaseClient=db, userId=uid)
        result = ext.pullCalData(external_id)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=result["error"]))
        inserted = result.get("inserted", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pulled {inserted} events into 'Google Calendar (Synced)'."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Sync failed: {err}"))


@ui_bp.route("/settings/external/google/<external_id>/push", methods=["POST"])
@ui_login_required
def settings_push_google(external_id):
    uid = _ui_user()["id"]
    try:
        db = get_supabase_client()
        ext = External(id=external_id, url="", provider="", supabaseClient=db, userId=uid)
        result = ext.pushCalData(external_id)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=result["error"]))
        pushed = result.get("pushed", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pushed {pushed} events to Google Calendar."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Push failed: {err}"))
