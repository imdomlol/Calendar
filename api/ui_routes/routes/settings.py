from flask import redirect, request, session, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _ui_user,
    _make_ui_user,
    _google_oauth_config,
    _outlook_oauth_config,
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


def _sync_error_message(error: str, provider: str) -> str:
    if error == "token_expired":
        return f"Your {provider} access has expired — please reconnect your account."
    return error


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
    outlook_rows = []
    try:
        u = _make_ui_user()
        all_externals = u.listExternals()
        google_rows = [e for e in all_externals if "google" in str(e.get("provider") or "").lower()]
        outlook_rows = [e for e in all_externals if "outlook" in str(e.get("provider") or "").lower()]
    except Exception as e:
        status = "error"
        message = f"Couldn't load externals: {e}"

    return render_page(
        "Settings", role, nav, "settings/auth.html",
        status=status,
        message=message,
        google_rows=google_rows,
        outlook_rows=outlook_rows,
    )


@ui_bp.route("/settings/external/google/connect", methods=["GET", "POST"])
@ui_login_required
def settings_connect_google():
    return settings_login_google()


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

        db = get_supabase_client()
        app_base_url = _resolve_app_base_url()
        lookup = External(id=None, supabaseClient=db, userId=uid)
        existing = lookup.findForUserProvider("google", provider_url)
        if existing:
            ext = External(id=existing["id"], supabaseClient=db, userId=uid)
            ext.updateTokens(existing["id"], uid,
                             accessToken=creds.get("access_token"),
                             refreshToken=creds.get("refresh_token"))
            ext.registerSubscription(existing["id"], app_base_url, clientId, client_secret)
            message = "Google connection refreshed."
        else:
            ext = External(id=None, supabaseClient=db, userId=uid)
            result = ext.save(url=provider_url, provider="google",
                              accessToken=creds.get("access_token"),
                              refreshToken=creds.get("refresh_token"))
            created_id = (result.data or [{}])[0].get("id")
            if not created_id:
                raise RuntimeError("Google connection was saved without an id")
            ext.registerSubscription(created_id, app_base_url, clientId, client_secret)
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
    client_id, client_secret = _google_oauth_config()
    try:
        db = get_supabase_client()
        ext = External(id=external_id, supabaseClient=db, userId=uid)
        result = ext.pullCalData(external_id, client_id=client_id, client_secret=client_secret)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=_sync_error_message(result["error"], "Google")))
        inserted = result.get("inserted", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pulled {inserted} events into 'Google Calendar (Synced)'."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Sync failed: {err}"))


@ui_bp.route("/settings/external/google/<external_id>/push", methods=["POST"])
@ui_login_required
def settings_push_google(external_id):
    uid = _ui_user()["id"]
    client_id, client_secret = _google_oauth_config()
    try:
        db = get_supabase_client()
        ext = External(id=external_id, supabaseClient=db, userId=uid)
        result = ext.pushCalData(external_id, client_id=client_id, client_secret=client_secret)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=_sync_error_message(result["error"], "Google")))
        pushed = result.get("pushed", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pushed {pushed} events to Google Calendar."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Push failed: {err}"))


def _clear_outlook_oauth_session():
    session.pop("outlook_oauth_state", None)
    session.pop("outlook_oauth_redirect_uri", None)


@ui_bp.route("/settings/external/azure/login")
@ui_login_required
def settings_login_outlook():
    clientId, client_secret = _outlook_oauth_config()
    if not clientId or not client_secret:
        return redirect(url_for("ui.settings_page", status="error",
                                message="Microsoft OAuth not configured, set MS_CLIENT_ID and MS_CLIENT_SECRET"))

    try:
        from requests_oauthlib import OAuth2Session
    except ImportError as e:
        return redirect(url_for("ui.settings_page", status="error", message=f"OAuth dep missing: {e}"))

    appBaseUrl = _resolve_app_base_url()
    redirect_uri = f"{appBaseUrl}{url_for('ui.settings_outlook_callback')}"

    oauth = OAuth2Session(
        clientId,
        redirect_uri=redirect_uri,
        scope=[
            "https://graph.microsoft.com/Calendars.ReadWrite",
            "offline_access",
        ],
    )
    authorization_url, state = oauth.authorization_url(
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        prompt="consent",
    )
    session["outlook_oauth_state"] = state
    session["outlook_oauth_redirect_uri"] = redirect_uri
    return redirect(authorization_url)


@ui_bp.route("/settings/external/azure/callback")
@ui_login_required
def settings_outlook_callback():
    exp_state = (session.get("outlook_oauth_state") or "").strip()
    ret_state = (request.args.get("state") or "").strip()
    if not exp_state or ret_state != exp_state:
        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message="OAuth state mismatch"))

    clientId, client_secret = _outlook_oauth_config()
    redirect_uri = (session.get("outlook_oauth_redirect_uri") or "").strip()

    try:
        from requests_oauthlib import OAuth2Session
    except Exception as err:
        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message=f"OAuth dep missing: {err}"))

    if not clientId or not client_secret or not redirect_uri:
        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="error",
                                message="OAuth session expired, missing clientId or redirect_uri"))

    try:
        oauth = OAuth2Session(clientId, redirect_uri=redirect_uri, state=exp_state)
        creds = oauth.fetch_token(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            client_secret=client_secret,
            authorization_response=request.url,
        )

        uid = _ui_user()["id"]
        provider_url = "https://graph.microsoft.com/v1.0"

        db = get_supabase_client()
        app_base_url = _resolve_app_base_url()
        lookup = External(id=None, supabaseClient=db, userId=uid)
        existing = lookup.findForUserProvider("outlook", provider_url)
        if existing:
            ext = External(id=existing["id"], supabaseClient=db, userId=uid)
            ext.updateTokens(existing["id"], uid,
                             accessToken=creds.get("access_token"),
                             refreshToken=creds.get("refresh_token"))
            ext.registerSubscription(existing["id"], app_base_url, clientId, client_secret)
            message = "Outlook connection refreshed."
        else:
            ext = External(id=None, supabaseClient=db, userId=uid)
            result = ext.save(url=provider_url, provider="outlook",
                              accessToken=creds.get("access_token"),
                              refreshToken=creds.get("refresh_token"))
            created_id = (result.data or [{}])[0].get("id")
            if not created_id:
                raise RuntimeError("Outlook connection was saved without an id")
            ext.registerSubscription(created_id, app_base_url, clientId, client_secret)
            message = f"Outlook connection created (id: {created_id})."

        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="ok", message=message))

    except Exception as exc:
        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="error", message=f"Outlook OAuth failed: {exc}"))


@ui_bp.route("/settings/external/outlook/<external_id>/sync", methods=["POST"])
@ui_login_required
def settings_sync_outlook(external_id):
    uid = _ui_user()["id"]
    client_id, client_secret = _outlook_oauth_config()
    try:
        db = get_supabase_client()
        ext = External(id=external_id, supabaseClient=db, userId=uid)
        result = ext.pullCalData(external_id, client_id=client_id, client_secret=client_secret)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=_sync_error_message(result["error"], "Outlook")))
        inserted = result.get("inserted", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pulled {inserted} events into 'Outlook Calendar (Synced)'."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Sync failed: {err}"))


@ui_bp.route("/settings/external/outlook/<external_id>/push", methods=["POST"])
@ui_login_required
def settings_push_outlook(external_id):
    uid = _ui_user()["id"]
    client_id, client_secret = _outlook_oauth_config()
    try:
        db = get_supabase_client()
        ext = External(id=external_id, supabaseClient=db, userId=uid)
        result = ext.pushCalData(external_id, client_id=client_id, client_secret=client_secret)
        if "error" in result:
            return redirect(url_for("ui.settings_page", status="error", message=_sync_error_message(result["error"], "Outlook")))
        pushed = result.get("pushed", 0)
        return redirect(url_for("ui.settings_page", status="ok",
                                message=f"Pushed {pushed} events to Outlook."))
    except Exception as err:
        return redirect(url_for("ui.settings_page", status="error", message=f"Push failed: {err}"))
