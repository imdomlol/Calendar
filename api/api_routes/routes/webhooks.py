import os
from flask import Response, request
from api.api_routes import api_bp
from models.external import External
from utils.logger import logEvent
from utils.renew_subscriptions import renewSubscriptions
from utils.supabase_client import get_supabase_client


def _google_oauth_config():
    clientId = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    clientSecret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    return clientId, clientSecret


def _outlook_oauth_config():
    clientId = (os.environ.get("MS_CLIENT_ID") or "").strip()
    clientSecret = (os.environ.get("MS_CLIENT_SECRET") or "").strip()
    return clientId, clientSecret


def _app_base_url():
    baseUrl = (os.environ.get("APP_BASE_URL") or "").strip().rstrip("/")
    if not baseUrl:
        baseUrl = request.url_root.rstrip("/")
    return baseUrl


@api_bp.route("/api/webhooks/google", methods=["POST"])
def googleWebhook():
    externalId = (request.headers.get("X-Goog-Channel-Token") or "").strip()
    if not externalId:
        logEvent("WARNING", "webhook_google", "Google webhook missing channel token",
                 path=request.path, method=request.method, statusCode=400)
        return "", 400
    try:
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")
        ext.pullWebhookData(externalId, googleClientId, googleClientSecret, outlookClientId, outlookClientSecret)
        logEvent("INFO", "webhook_google", "Google webhook sync finished",
                 details={"external_id": externalId})
        return "", 200
    except Exception as err:
        logEvent("ERROR", "webhook_google", "Google webhook sync failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"external_id": externalId, "error": str(err)})
        return "", 500


@api_bp.route("/api/webhooks/outlook", methods=["POST"])
def outlookWebhook():
    validationToken = request.args.get("validationToken")
    if validationToken:
        return Response(validationToken, status=200, mimetype="text/plain")
    try:
        body = request.get_json(silent=True) or {}
        values = body.get("value") or []
        if not values:
            logEvent("WARNING", "webhook_outlook", "Outlook webhook missing value list",
                     path=request.path, method=request.method, statusCode=400)
            return "", 400
        firstValue = values[0]
        externalId = (firstValue.get("clientState") or "").strip()
        if not externalId:
            logEvent("WARNING", "webhook_outlook", "Outlook webhook missing client state",
                     path=request.path, method=request.method, statusCode=400)
            return "", 400
        googleClientId, googleClientSecret = _google_oauth_config()
        outlookClientId, outlookClientSecret = _outlook_oauth_config()
        db = get_supabase_client()
        ext = External(id=externalId, supabaseClient=db, userId="")
        ext.pullWebhookData(externalId, googleClientId, googleClientSecret, outlookClientId, outlookClientSecret)
        logEvent("INFO", "webhook_outlook", "Outlook webhook sync finished",
                 details={"external_id": externalId})
        return "", 202
    except Exception as err:
        logEvent("ERROR", "webhook_outlook", "Outlook webhook sync failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"error": str(err)})
        return "", 500


@api_bp.route("/api/cron/renew-subscriptions", methods=["GET", "POST"])
def renewSubscriptionsCron():
    expectedSecret = (os.environ.get("CRON_SECRET") or "").strip()
    givenSecret = (request.headers.get("X-Cron-Secret") or "").strip()
    if not expectedSecret:
        logEvent("ERROR", "webhook_subscription", "CRON_SECRET is not configured",
                 path=request.path, method=request.method, statusCode=500)
        return {"error": "cron secret is not configured"}, 500
    if givenSecret != expectedSecret:
        logEvent("WARNING", "webhook_subscription", "Bad cron secret",
                 path=request.path, method=request.method, statusCode=403)
        return {"error": "forbidden"}, 403
    try:
        result = renewSubscriptions(_app_base_url())
        return result, 200
    except Exception as err:
        logEvent("ERROR", "webhook_subscription", "Subscription renewal failed",
                 path=request.path, method=request.method, statusCode=500,
                 details={"error": str(err)})
        return {"error": "renewal failed"}, 500
