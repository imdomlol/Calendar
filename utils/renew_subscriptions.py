import os
from datetime import datetime, timedelta, timezone
from models.external import External
from utils.logger import logEvent
from utils.supabase_client import get_supabase_client


def renewSubscriptions(appBaseUrl: str):
    db = get_supabase_client()
    cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
    cutoffText = cutoff.isoformat()
    result = db.table("externals").select("*").lte("subscription_expires", cutoffText).execute()
    rows = result.data or []
    renewed = 0
    failed = 0
    for row in rows:
        externalId = row.get("id")
        userId = row.get("user_id")
        if not externalId or not userId:
            continue
        try:
            ext = External(id=externalId, supabaseClient=db, userId=userId)
            provider = (row.get("provider") or "").lower()
            if provider == "google":
                clientId = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
                clientSecret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
            elif provider == "outlook":
                clientId = (os.environ.get("MS_CLIENT_ID") or "").strip()
                clientSecret = (os.environ.get("MS_CLIENT_SECRET") or "").strip()
            else:
                clientId = ""
                clientSecret = ""
            ext.registerSubscription(externalId, appBaseUrl, clientId, clientSecret)
            renewed = renewed + 1
        except Exception as err:
            failed = failed + 1
            logEvent("ERROR", "webhook_subscription", "Could not renew subscription",
                     userId=userId, details={"external_id": externalId, "error": str(err)})
    return {
        "renewed": renewed,
        "failed": failed,
    }
