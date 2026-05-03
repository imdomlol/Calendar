import os
from flask import Response, request
from api.api_routes import api_bp
from models.external import External
from utils.logger import log_event
from utils.renew_subscriptions import renewSubscriptions
from utils.supabase_client import get_supabase_client


# ========================= Config Helpers =========================

# read the Google OAuth client values
# returns client id then client secret
def _google_oauth_config():
    # grab the Google client id and clean it up
    rawId = os.environ.get("GOOGLE_CLIENT_ID")
    if rawId is None:
        rawId = ""
    clientId = rawId.strip()

    # grab the Google client secret too
    rawSecret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if rawSecret is None:
        rawSecret = ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret


# read the Outlook OAuth client values
# returns client id then client secret
def _outlook_oauth_config():
    # grab the Microsoft client id and clean it up
    rawId = os.environ.get("MS_CLIENT_ID")
    if rawId is None:
        rawId = ""
    clientId = rawId.strip()

    # grab the Microsoft client secret too
    rawSecret = os.environ.get("MS_CLIENT_SECRET")
    if rawSecret is None:
        rawSecret = ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret


# figure out the public base URL for callback links
def _app_base_url():
    # start with the configured URL if one exists
    rawUrl = os.environ.get("APP_BASE_URL")
    if rawUrl is None:
        rawUrl = ""
    trimmed = rawUrl.strip()
    baseUrl = trimmed.rstrip("/")

    # fall back to the current request URL root
    if not baseUrl:
        urlRoot = request.url_root
        baseUrl = urlRoot.rstrip("/")
    return baseUrl


# ========================= Webhook Routes =========================

# receive push notifications from Google Calendar
# the channel token tells us which external calendar changed
@api_bp.route("/api/webhooks/google", methods=["POST"])
def google_webhook():
    # read the channel token Google sent
    rawToken = request.headers.get("X-Goog-Channel-Token")
    if rawToken is None:
        rawToken = ""
    externalId = rawToken.strip()

    # reject the request when we cannot match the calendar
    if not externalId:
        log_event(
            "WARNING",
            "webhook_google",
            "Google webhook missing channel token",
            path=request.path,
            method=request.method,
            statusCode=400,
        )
        return "", 400

    try:
        # load OAuth credentials before making calendar API calls
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()

        # build the external calendar helper
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")

        # pull the changed calendar data into our DB
        ext.pull_webhook_data(
            externalId,
            googleClientId,
            googleClientSecret,
            outlookClientId,
            outlookClientSecret,
        )
        log_event(
            "INFO",
            "webhook_google",
            "Google webhook sync finished",
            details={"external_id": externalId},
        )
        return "", 200
    except Exception as err:
        # save the real error in logs
        log_event(
            "ERROR",
            "webhook_google",
            "Google webhook sync failed",
            path=request.path,
            method=request.method,
            statusCode=500,
            details={"external_id": externalId, "error": str(err)},
        )
        return "", 500


# receive push notifications from Microsoft Outlook
# the first request can be a validation handshake
@api_bp.route("/api/webhooks/outlook", methods=["POST"])
def outlook_webhook():
    # echo the validation token so Outlook accepts this URL
    validationToken = request.args.get("validationToken")
    if validationToken:
        return Response(validationToken, status=200, mimetype="text/plain")

    try:
        # parse the JSON body from Outlook
        body = request.get_json(silent=True)
        if body is None:
            body = {}

        # Outlook puts notifications inside value
        rawValues = body.get("value")
        if rawValues:
            values = rawValues
        else:
            values = []

        # reject empty notification batches
        if not values:
            log_event(
                "WARNING",
                "webhook_outlook",
                "Outlook webhook missing value list",
                path=request.path,
                method=request.method,
                statusCode=400,
            )
            return "", 400

        # use the first notification to find the external record
        firstValue = values[0]

        # clientState holds the external id we sent earlier
        rawState = firstValue.get("clientState")
        if rawState is None:
            rawState = ""
        externalId = rawState.strip()

        # reject the request when the external id is missing
        if not externalId:
            log_event(
                "WARNING",
                "webhook_outlook",
                "Outlook webhook missing client state",
                path=request.path,
                method=request.method,
                statusCode=400,
            )
            return "", 400

        # load OAuth credentials before calendar API calls
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()

        # build the external calendar helper
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")

        # pull the changed calendar data into our DB
        ext.pull_webhook_data(
            externalId,
            googleClientId,
            googleClientSecret,
            outlookClientId,
            outlookClientSecret,
        )
        log_event(
            "INFO",
            "webhook_outlook",
            "Outlook webhook sync finished",
            details={"external_id": externalId},
        )

        # Outlook expects 202 for accepted webhook notifications
        return "", 202
    except Exception as err:
        # keep the response simple but log the real error
        log_event(
            "ERROR",
            "webhook_outlook",
            "Outlook webhook sync failed",
            path=request.path,
            method=request.method,
            statusCode=500,
            details={"error": str(err)},
        )
        return "", 500


# ========================= Cron Routes =========================

# renew expiring calendar subscriptions from cron
# the shared secret keeps this endpoint private
@api_bp.route("/api/cron/renew-subscriptions", methods=["GET", "POST"])
def renew_subscriptions_cron():
    # read the secret we expect callers to send
    rawExpected = os.environ.get("CRON_SECRET")
    if rawExpected is None:
        rawExpected = ""
    expectedSecret = rawExpected.strip()

    # Vercel cron jobs send the secret as "Authorization: Bearer <CRON_SECRET>"
    rawGiven = request.headers.get("Authorization")
    if rawGiven is None:
        rawGiven = ""
    # strip the "Bearer " prefix if present
    bearer = rawGiven.strip()
    if bearer.lower().startswith("bearer "):
        givenSecret = bearer[7:].strip()
    else:
        givenSecret = bearer

    # fail when the server is missing its cron secret
    if not expectedSecret:
        log_event(
            "ERROR",
            "webhook_subscription",
            "CRON_SECRET is not configured",
            path=request.path,
            method=request.method,
            statusCode=500,
        )
        return {"error": "cron secret is not configured"}, 500

    # refuse callers with the wrong secret
    if givenSecret != expectedSecret:
        log_event(
            "WARNING",
            "webhook_subscription",
            "Bad cron secret",
            path=request.path,
            method=request.method,
            statusCode=403,
        )
        return {"error": "forbidden"}, 403

    try:
        # run renewal and return the summary
        result = renewSubscriptions(_app_base_url())
        return result, 200
    except Exception as err:
        # log the details without exposing them through the API
        log_event(
            "ERROR",
            "webhook_subscription",
            "Subscription renewal failed",
            path=request.path,
            method=request.method,
            statusCode=500,
            details={"error": str(err)},
        )
        return {"error": "renewal failed"}, 500
