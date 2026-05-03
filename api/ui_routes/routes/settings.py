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
)
from models.external import External
from utils.supabase_client import get_supabase_client


# ========================= Shared Helpers =========================


# clear saved Google OAuth data from the browser session
def _clear_oauth_session():
    session.pop("google_oauth_state", None)
    session.pop("google_oauth_redirect_uri", None)


# make token errors easier for users to understand
def _sync_error_message(error: str, provider: str) -> str:
    if error == "token_expired":
        return f"Your {provider} access has expired, please reconnect your account."

    return error


# ========================= Settings Page =========================


@ui_bp.route("/settings")
def settings_page():
    # show the guest settings page when nobody is logged in
    user = _ui_user()

    if not user:
        return render_page("Settings", "settings/guest.html")

    status = (request.args.get("status") or "").strip()
    message = (request.args.get("message") or "").strip()
    googleRows = []
    outlookRows = []

    try:
        # load the connected external accounts for this user
        uiUser = _make_ui_user()
        allExternals = uiUser.listExternals()

        # split providers into the two tables shown on the page
        for externalRow in allExternals:
            # normalize the provider so text checks are simple
            rawProvider = externalRow.get("provider") or ""
            providerName = str(rawProvider).lower()

            if "google" in providerName:
                googleRows.append(externalRow)

            if "outlook" in providerName:
                outlookRows.append(externalRow)
    except Exception as error:
        status = "error"
        message = f"Couldn't load externals: {error}"

    return render_page(
        "Settings",
        "settings/auth.html",
        status=status,
        message=message,
        google_rows=googleRows,
        outlook_rows=outlookRows,
    )


# ========================= Google OAuth Routes =========================


@ui_bp.route("/settings/external/google/connect", methods=["GET", "POST"])
@ui_login_required
def settings_connect_google():
    # old connect route still sends users through the normal Google login
    return settings_login_google()


@ui_bp.route("/settings/external/google/login")
@ui_login_required
def settings_login_google():
    # grab the app credentials before building the OAuth request
    clientId, clientSecret = _google_oauth_config()

    # both values are needed before Google can start OAuth
    if not clientId or not clientSecret:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="Google OAuth not configured, set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET",
            )
        )

    try:
        from requests_oauthlib import OAuth2Session
    except ImportError as error:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dep missing: {error}",
            )
        )

    appBaseUrl = _resolve_app_base_url()
    redirectUri = f"{appBaseUrl}{url_for('ui.settings_google_callback')}"

    # ask Google for calendar access and a refresh token
    oauth = OAuth2Session(
        clientId,
        redirect_uri=redirectUri,
        scope=[
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
    )
    authorizationUrl, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="consent",
    )

    session["google_oauth_state"] = state
    session["google_oauth_redirect_uri"] = redirectUri
    return redirect(authorizationUrl)


@ui_bp.route("/settings/external/google/callback")
@ui_login_required
def settings_google_callback():
    # compare the state values so a different request cannot finish this login
    expectedState = (session.get("google_oauth_state") or "").strip()
    returnedState = (request.args.get("state") or "").strip()

    # stop if the session state is missing or different
    if not expectedState or returnedState != expectedState:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="OAuth state mismatch",
            )
        )

    clientId, clientSecret = _google_oauth_config()
    redirectUri = (session.get("google_oauth_redirect_uri") or "").strip()

    try:
        from requests_oauthlib import OAuth2Session
    except Exception as error:
        # clear the partial OAuth session before showing the error
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dep missing: {error}",
            )
        )

    # all three values are required to trade the code for tokens
    if not clientId or not clientSecret or not redirectUri:
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="OAuth session expired, missing clientId or redirect_uri",
            )
        )

    try:
        # trade the callback URL for OAuth tokens
        oauth = OAuth2Session(
            clientId,
            redirect_uri=redirectUri,
            state=expectedState,
        )
        creds = oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=clientSecret,
            authorization_response=request.url,
        )

        userId = _ui_user()["id"]
        providerUrl = "https://www.googleapis.com/calendar/v3"

        # find any existing Google connection for this user
        db = get_supabase_client()
        appBaseUrl = _resolve_app_base_url()
        lookup = External(id=None, supabaseClient=db, userId=userId)
        existing = lookup.find_for_user_provider("google", providerUrl)

        if existing:
            ext = External(id=existing["id"], supabaseClient=db, userId=userId)
            ext.update_tokens(
                existing["id"],
                userId,
                accessToken=creds.get("access_token"),
                refreshToken=creds.get("refresh_token"),
            )
            ext.register_subscription(
                existing["id"],
                appBaseUrl,
                clientId,
                clientSecret,
            )
            message = "Google connection refreshed."
        else:
            # make a new external row when the user has no saved Google link
            ext = External(id=None, supabaseClient=db, userId=userId)
            result = ext.save(
                url=providerUrl,
                provider="google",
                accessToken=creds.get("access_token"),
                refreshToken=creds.get("refresh_token"),
            )

            resultRows = result.data or [{}]
            createdId = resultRows[0].get("id")

            # the saved row must have an id so the webhook can be registered
            if not createdId:
                raise RuntimeError("Google connection was saved without an id")

            ext.register_subscription(createdId, appBaseUrl, clientId, clientSecret)
            message = f"Google connection created (id: {createdId})."

        _clear_oauth_session()
        return redirect(url_for("ui.settings_page", status="ok", message=message))

    except Exception as error:
        # clear this login attempt if anything in the callback fails
        _clear_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"Google OAuth failed: {error}",
            )
        )


# ========================= Google Sync Routes =========================


@ui_bp.route("/settings/external/google/<externalId>/sync", methods=["POST"])
@ui_login_required
def settings_sync_google(externalId):
    # sync from Google into this app
    userId = _ui_user()["id"]
    clientId, clientSecret = _google_oauth_config()

    try:
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId=userId)
        result = ext.pull_cal_data(
            externalId,
            client_id=clientId,
            client_secret=clientSecret,
        )

        # show a clearer message when the provider returned a known error
        if "error" in result:
            message = _sync_error_message(result["error"], "Google")
            return redirect(url_for("ui.settings_page", status="error", message=message))

        inserted = result.get("inserted", 0)
        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pulled {inserted} events into 'Google Calendar (Synced)'.",
            )
        )
    except Exception as error:
        # send unexpected sync errors back to the settings page
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Sync failed: {error}")
        )


@ui_bp.route("/settings/external/google/<externalId>/push", methods=["POST"])
@ui_login_required
def settings_push_google(externalId):
    # push local event changes back to Google
    userId = _ui_user()["id"]
    clientId, clientSecret = _google_oauth_config()

    try:
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId=userId)
        result = ext.push_cal_data(
            externalId,
            client_id=clientId,
            client_secret=clientSecret,
        )

        # turn known token errors into friendlier page text
        if "error" in result:
            message = _sync_error_message(result["error"], "Google")
            return redirect(url_for("ui.settings_page", status="error", message=message))

        pushed = result.get("pushed", 0)
        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pushed {pushed} events to Google Calendar.",
            )
        )
    except Exception as error:
        # report the push problem without leaving this page
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Push failed: {error}")
        )


# ========================= Outlook OAuth Routes =========================


# clear saved Outlook OAuth values from the session
def _clear_outlook_oauth_session():
    session.pop("outlook_oauth_state", None)
    session.pop("outlook_oauth_redirect_uri", None)


@ui_bp.route("/settings/external/azure/login")
@ui_login_required
def settings_login_outlook():
    # grab Microsoft credentials for the OAuth flow
    clientId, clientSecret = _outlook_oauth_config()

    # Microsoft needs both OAuth settings before redirecting
    if not clientId or not clientSecret:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="Microsoft OAuth not configured, set MS_CLIENT_ID and MS_CLIENT_SECRET",
            )
        )

    try:
        from requests_oauthlib import OAuth2Session
    except ImportError as error:
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dep missing: {error}",
            )
        )

    appBaseUrl = _resolve_app_base_url()
    redirectUri = f"{appBaseUrl}{url_for('ui.settings_outlook_callback')}"

    # ask Microsoft for calendar access and offline refresh
    oauth = OAuth2Session(
        clientId,
        redirect_uri=redirectUri,
        scope=[
            "https://graph.microsoft.com/Calendars.ReadWrite",
            "offline_access",
        ],
    )
    authorizationUrl, state = oauth.authorization_url(
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        prompt="consent",
    )

    session["outlook_oauth_state"] = state
    session["outlook_oauth_redirect_uri"] = redirectUri
    return redirect(authorizationUrl)


@ui_bp.route("/settings/external/azure/callback")
@ui_login_required
def settings_outlook_callback():
    # check that the callback belongs to the login we started
    expectedState = (session.get("outlook_oauth_state") or "").strip()
    returnedState = (request.args.get("state") or "").strip()

    # reject callbacks that do not match this browser session
    if not expectedState or returnedState != expectedState:
        _clear_outlook_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="OAuth state mismatch",
            )
        )

    clientId, clientSecret = _outlook_oauth_config()
    redirectUri = (session.get("outlook_oauth_redirect_uri") or "").strip()

    try:
        from requests_oauthlib import OAuth2Session
    except Exception as error:
        # clear the saved callback details before leaving
        _clear_outlook_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"OAuth dep missing: {error}",
            )
        )

    # the callback cannot finish without credentials and the redirect URI
    if not clientId or not clientSecret or not redirectUri:
        _clear_outlook_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message="OAuth session expired, missing clientId or redirect_uri",
            )
        )

    try:
        # trade the Microsoft callback URL for tokens
        oauth = OAuth2Session(
            clientId,
            redirect_uri=redirectUri,
            state=expectedState,
        )
        creds = oauth.fetch_token(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            client_secret=clientSecret,
            authorization_response=request.url,
        )

        userId = _ui_user()["id"]
        providerUrl = "https://graph.microsoft.com/v1.0"

        # create or refresh the saved Outlook connection
        db = get_supabase_client()
        appBaseUrl = _resolve_app_base_url()
        lookup = External(id=None, supabaseClient=db, userId=userId)
        existing = lookup.find_for_user_provider("outlook", providerUrl)

        if existing:
            ext = External(id=existing["id"], supabaseClient=db, userId=userId)
            ext.update_tokens(
                existing["id"],
                userId,
                accessToken=creds.get("access_token"),
                refreshToken=creds.get("refresh_token"),
            )
            ext.register_subscription(
                existing["id"],
                appBaseUrl,
                clientId,
                clientSecret,
            )
            message = "Outlook connection refreshed."
        else:
            # save a fresh Outlook connection for this user
            ext = External(id=None, supabaseClient=db, userId=userId)
            result = ext.save(
                url=providerUrl,
                provider="outlook",
                accessToken=creds.get("access_token"),
                refreshToken=creds.get("refresh_token"),
            )

            resultRows = result.data or [{}]
            createdId = resultRows[0].get("id")

            # subscription setup needs the id from the new row
            if not createdId:
                raise RuntimeError("Outlook connection was saved without an id")

            ext.register_subscription(createdId, appBaseUrl, clientId, clientSecret)
            message = f"Outlook connection created (id: {createdId})."

        _clear_outlook_oauth_session()
        return redirect(url_for("ui.settings_page", status="ok", message=message))

    except Exception as error:
        # clean up any temporary OAuth state after a callback error
        _clear_outlook_oauth_session()
        return redirect(
            url_for(
                "ui.settings_page",
                status="error",
                message=f"Outlook OAuth failed: {error}",
            )
        )


# ========================= Outlook Sync Routes =========================


@ui_bp.route("/settings/external/outlook/<externalId>/sync", methods=["POST"])
@ui_login_required
def settings_sync_outlook(externalId):
    # sync Outlook calendar data into this app
    userId = _ui_user()["id"]
    clientId, clientSecret = _outlook_oauth_config()

    try:
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId=userId)
        result = ext.pull_cal_data(
            externalId,
            client_id=clientId,
            client_secret=clientSecret,
        )

        # make known provider errors easier to read
        if "error" in result:
            message = _sync_error_message(result["error"], "Outlook")
            return redirect(url_for("ui.settings_page", status="error", message=message))

        inserted = result.get("inserted", 0)
        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pulled {inserted} events into 'Outlook Calendar (Synced)'.",
            )
        )
    except Exception as error:
        # keep the error visible on the settings page
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Sync failed: {error}")
        )


@ui_bp.route("/settings/external/outlook/<externalId>/push", methods=["POST"])
@ui_login_required
def settings_push_outlook(externalId):
    # push this app events back to Outlook
    userId = _ui_user()["id"]
    clientId, clientSecret = _outlook_oauth_config()

    try:
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId=userId)
        result = ext.push_cal_data(
            externalId,
            client_id=clientId,
            client_secret=clientSecret,
        )

        # show the friendly version of known push errors
        if "error" in result:
            message = _sync_error_message(result["error"], "Outlook")
            return redirect(url_for("ui.settings_page", status="error", message=message))

        pushed = result.get("pushed", 0)
        return redirect(
            url_for(
                "ui.settings_page",
                status="ok",
                message=f"Pushed {pushed} events to Outlook.",
            )
        )
    except Exception as error:
        # report the unexpected push failure to the user
        return redirect(
            url_for("ui.settings_page", status="error", message=f"Push failed: {error}")
        )
