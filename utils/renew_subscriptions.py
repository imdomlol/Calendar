import os
from datetime import datetime, timedelta, timezone
from models.external import External
from utils.logger import log_event
from utils.supabase_client import get_supabase_client


# ========================= Subscription Renewal =========================

# checks all externals expiring in the next 24 hours and re-registers their webhooks
def renew_subscriptions(appBaseUrl: str):
    db = get_supabase_client()

    # find everything that expires within the next 24 hours
    cutoff = datetime.now(timezone.utc) + timedelta(hours=24)
    cutoffText = cutoff.isoformat()

    # query the externals table for rows expiring at or before the cutoff
    query = db.table("externals").select("*").lte("subscription_expires", cutoffText)
    result = query.execute()
    rows = result.data or []

    renewed = 0
    failed = 0

    for row in rows:
        externalId = row.get("id")
        userId = row.get("user_id")

        # skip rows missing required ids
        if not externalId or not userId:
            continue

        try:
            ext = External(id=externalId, supabaseClient=db, userId=userId)

            # look up the right OAuth credentials based on which provider this is
            provider = row.get("provider") or ""
            provider = provider.lower()

            if provider == "google":
                clientId = os.environ.get("GOOGLE_CLIENT_ID") or ""
                clientId = clientId.strip()
                clientSecret = os.environ.get("GOOGLE_CLIENT_SECRET") or ""
                clientSecret = clientSecret.strip()
            elif provider == "outlook":
                clientId = os.environ.get("MS_CLIENT_ID") or ""
                clientId = clientId.strip()
                clientSecret = os.environ.get("MS_CLIENT_SECRET") or ""
                clientSecret = clientSecret.strip()
            else:
                clientId = ""
                clientSecret = ""

            ext.register_subscription(externalId, appBaseUrl, clientId, clientSecret)
            renewed = renewed + 1
        except Exception as err:
            failed = failed + 1
            
            log_event(
                "ERROR",
                "webhook_subscription",
                "Could not renew subscription",
                userId=userId,
                details={"external_id": externalId, "error": str(err)},
            )

    return {
        "renewed": renewed,
        "failed": failed,
    }
