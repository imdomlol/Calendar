import os
from flask import Response, request
from api.api_routes import api_bp
from models.external import External
from utils.logger import log_event
from utils.renew_subscriptions import renewSubscriptions
from utils.supabase_client import get_supabase_client


# ========================= config helpers =========================

# this function reads the Google OAuth client id and secret from the environment
# it is called before any Google Calendar sync so we have the credentials ready
# it returns both values as a tuple in the order (client id, client secret)
def _google_oauth_config():
    # grab the Google client id from the environment and remove surrounding whitespace
    rawId = os.environ.get("GOOGLE_CLIENT_ID") or ""
    clientId = rawId.strip()
    # grab the Google client secret from the environment and remove surrounding whitespace
    rawSecret = os.environ.get("GOOGLE_CLIENT_SECRET") or ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret

# this function reads the Microsoft Outlook OAuth client id and secret from the environment
# it is called before any Outlook Calendar sync so we have the credentials ready
# it returns both values as a tuple in the order (client id, client secret)
def _outlook_oauth_config():
    # grab the Microsoft client id from the environment and remove surrounding whitespace
    rawId = os.environ.get("MS_CLIENT_ID") or ""
    clientId = rawId.strip()
    # grab the Microsoft client secret from the environment and remove surrounding whitespace
    rawSecret = os.environ.get("MS_CLIENT_SECRET") or ""
    clientSecret = rawSecret.strip()
    return clientId, clientSecret

# this function figures out what base URL the app is running at
# it checks the APP_BASE_URL environment variable first and falls back to the request URL
# the trailing slash is removed so we can safely append paths onto the result
def _app_base_url():
    # try to read the base URL from the environment and clean it up
    rawUrl = os.environ.get("APP_BASE_URL") or ""
    trimmed = rawUrl.strip()
    baseUrl = trimmed.rstrip("/")
    # if the environment variable was empty use the URL root from the current request
    if not baseUrl:
        baseUrl = request.url_root.rstrip("/")
    return baseUrl


# ========================= webhook routes =========================

# this route receives push notifications from Google Calendar
# Google sends a POST request here whenever a calendar the app is watching has changed
# the channel token in the header tells us which external calendar record to sync
@api_bp.route("/api/webhooks/google", methods=["POST"])
def google_webhook():
    # read the channel token Google sent and remove any surrounding whitespace
    rawToken = request.headers.get("X-Goog-Channel-Token") or ""
    externalId = rawToken.strip()
    # if there is no channel token we do not know which calendar changed so we reject the request
    if not externalId:
        log_event("WARNING", "webhook_google", "Google webhook missing channel token",
                 path=request.path, method=request.method, statusCode=400)
        return "", 400
    try:
        # load the OAuth credentials for both Google and Outlook before making any API calls
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()
        # open a database connection and create an External object for this channel
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")
        # tell the External object to fetch the latest calendar data and store it
        ext.pull_webhook_data(externalId, googleClientId, googleClientSecret, outlookClientId, outlookClientSecret)
        log_event("INFO", "webhook_google", "Google webhook sync finished",
                 details={"external_id": externalId})
        return "", 200
    except Exception as err:
        log_event("ERROR", "webhook_google", "Google webhook sync failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"external_id": externalId, "error": str(err)})
        return "", 500

# this route receives push notifications from Microsoft Outlook
# Outlook sends a POST request here whenever something changes on a subscribed calendar
# the very first request Outlook sends is a validation handshake that we must echo back
@api_bp.route("/api/webhooks/outlook", methods=["POST"])
def outlook_webhook():
    # Outlook sends a validationToken query param the first time to verify we own this URL
    # we have to send it back as plain text so Outlook knows the endpoint is real
    validationToken = request.args.get("validationToken")
    if validationToken:
        return Response(validationToken, status=200, mimetype="text/plain")
    try:
        # parse the JSON body from the request and use an empty dict if the body is missing
        body = request.get_json(silent=True) or {}
        # Outlook wraps the change notifications inside a list called "value"
        rawValues = body.get("value")
        if rawValues:
            values = rawValues
        else:
            values = []
        # if there are no notifications there is nothing to sync so we reject the request
        if not values:
            log_event("WARNING", "webhook_outlook", "Outlook webhook missing value list",
                     path=request.path, method=request.method, statusCode=400)
            return "", 400
        # look at the first notification to find out which external calendar was affected
        firstValue = values[0]
        # Outlook puts our external id inside the clientState field so we read it here
        rawState = firstValue.get("clientState") or ""
        externalId = rawState.strip()
        # if there is no external id we cannot look up the calendar record so we reject
        if not externalId:
            log_event("WARNING", "webhook_outlook", "Outlook webhook missing client state",
                     path=request.path, method=request.method, statusCode=400)
            return "", 400
        # load the OAuth credentials for both Google and Outlook before making any API calls
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()
        # open a database connection and create an External object for this calendar
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")
        # tell the External object to fetch the latest calendar data and store it
        ext.pull_webhook_data(externalId, googleClientId, googleClientSecret, outlookClientId, outlookClientSecret)
        log_event("INFO", "webhook_outlook", "Outlook webhook sync finished",
                 details={"external_id": externalId})
        # Outlook expects 202 Accepted for successful webhook notifications not 200 OK
        return "", 202
    except Exception as err:
        log_event("ERROR", "webhook_outlook", "Outlook webhook sync failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"error": str(err)})
        return "", 500


# ========================= cron routes =========================

# this route is called by a scheduled cron job to renew expiring calendar subscriptions
# both Google and Outlook subscriptions expire after a set period so they need regular renewal
# the route is protected by a shared secret so only our own cron job can trigger it
@api_bp.route("/api/cron/renew-subscriptions", methods=["GET", "POST"])
def renew_subscriptions_cron():
    # read the secret we expect callers to send from the environment variable
    rawExpected = os.environ.get("CRON_SECRET") or ""
    expectedSecret = rawExpected.strip()
    # read the secret the caller actually sent in the request header
    rawGiven = request.headers.get("X-Cron-Secret") or ""
    givenSecret = rawGiven.strip()
    # if the environment variable is missing the server is misconfigured so we bail out
    if not expectedSecret:
        log_event("ERROR", "webhook_subscription", "CRON_SECRET is not configured",
                 path=request.path, method=request.method, statusCode=500)
        return {"error": "cron secret is not configured"}, 500
    # if the caller sent the wrong secret we refuse to run the renewal
    if givenSecret != expectedSecret:
        log_event("WARNING", "webhook_subscription", "Bad cron secret",
                 path=request.path, method=request.method, statusCode=403)
        return {"error": "forbidden"}, 403
    try:
        # run the renewal logic and return whatever summary it produces
        result = renewSubscriptions(_app_base_url())
        return result, 200
    except Exception as err:
        log_event("ERROR", "webhook_subscription", "Subscription renewal failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"error": str(err)})
        return {"error": "renewal failed"}, 500
