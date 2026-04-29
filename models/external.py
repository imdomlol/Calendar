from datetime import datetime, timedelta, timezone
from random import randint
import requests
from typing import Any
from uuid import uuid4
from utils.logger import logEvent


class External:
    def __init__(
        self,
        id: str | None,
        supabaseClient: Any,
        userId: str,
    ) -> None:
        self.id = id
        self.userId = userId
        self.supabaseClient = supabaseClient

    def save(self, url: str, provider: str, accessToken: str | None = None, refreshToken: str | None = None) -> Any:
        # insert this external connection into the database
        record = {
            "url": url,
            "provider": provider,
            "user_id": self.userId,
            "access_token": accessToken,
            "refresh_token": refreshToken,
        }
        if self.id is not None:
            record["id"] = self.id
        return self.supabaseClient.table("externals").insert(record).execute()

    def findForUserProvider(self, provider: str, url: str):
        db = self.supabaseClient
        result = db.table("externals").select("*").eq("user_id", self.userId).eq("provider", provider).eq("url", url).limit(1).execute()
        if result.data:
            return result.data[0]
        return None

    def updateSubscription(self, externalId: str, userId: str, subscriptionId: str | None, subscriptionExpires: str | None, resourceId: str | None = None) -> Any:
        db = self.supabaseClient
        updateData = {}
        updateData["subscription_id"] = subscriptionId
        updateData["subscription_expires"] = subscriptionExpires
        updateData["resource_id"] = resourceId
        return db.table("externals").update(updateData).eq("id", externalId).eq("user_id", userId).execute()

    def _subscription_url(self, appBaseUrl: str, provider: str) -> str:
        cleanBaseUrl = appBaseUrl.strip().rstrip("/")
        if provider == "google":
            return cleanBaseUrl + "/api/webhooks/google"
        return cleanBaseUrl + "/api/webhooks/outlook"

    def registerSubscription(self, externalId: str, appBaseUrl: str, clientId: str = "", clientSecret: str = "") -> Any:
        db = self.supabaseClient
        result = db.table("externals").select("*").eq("id", externalId).eq("user_id", self.userId).limit(1).execute()
        if not result.data:
            raise ValueError("External not found or not owned by user")
        extData = result.data[0]
        provider = (extData.get("provider") or "").lower()
        if provider == "google":
            return self._registerGoogleSubscription(extData, appBaseUrl, clientId, clientSecret)
        if provider == "outlook":
            return self._registerOutlookSubscription(extData, appBaseUrl, clientId, clientSecret)
        raise ValueError("Provider does not support webhooks")

    def _registerGoogleSubscription(self, extData: dict, appBaseUrl: str, clientId: str, clientSecret: str) -> Any:
        accessToken = extData.get("access_token")
        externalId = extData.get("id")
        userId = extData.get("user_id")
        if not accessToken:
            raise ValueError("Google access token is missing")
        channelId = str(uuid4())
        address = self._subscription_url(appBaseUrl, "google")
        body = {
            "id": channelId,
            "type": "web_hook",
            "address": address,
            "token": externalId,
        }
        headers = {
            "Authorization": "Bearer " + accessToken,
            "Content-Type": "application/json",
        }
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch"
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 401:
            newToken = self._refresh_access_token(extData, clientId, clientSecret)
            if newToken:
                extData["access_token"] = newToken
                headers["Authorization"] = "Bearer " + newToken
                response = requests.post(url, headers=headers, json=body)
        if response.status_code not in (200, 201):
            logEvent("ERROR", "webhook_subscription", "Google subscription registration failed",
                     userId=userId, details={"external_id": externalId, "status_code": response.status_code})
            raise RuntimeError("Google subscription registration failed")
        data = response.json()
        expires = None
        expiration = data.get("expiration")
        if expiration:
            expiresAt = datetime.fromtimestamp(int(expiration) / 1000, timezone.utc)
            expires = expiresAt.isoformat()
        subscriptionId = data.get("id")
        resourceId = data.get("resourceId")
        self.updateSubscription(externalId, userId, subscriptionId, expires, resourceId)
        self.stopSubscription(extData)
        logEvent("INFO", "webhook_subscription", "Google subscription registered",
                 userId=userId, details={"external_id": externalId, "subscription_id": subscriptionId})
        return data

    def _registerOutlookSubscription(self, extData: dict, appBaseUrl: str, clientId: str, clientSecret: str) -> Any:
        accessToken = extData.get("access_token")
        externalId = extData.get("id")
        userId = extData.get("user_id")
        if not accessToken:
            raise ValueError("Outlook access token is missing")
        jitterMinutes = randint(0, 120)
        expiresAt = datetime.now(timezone.utc) + timedelta(days=2, hours=23) - timedelta(minutes=jitterMinutes)
        expires = expiresAt.isoformat().replace("+00:00", "Z")
        address = self._subscription_url(appBaseUrl, "outlook")
        body = {
            "changeType": "created,updated,deleted",
            "notificationUrl": address,
            "resource": "me/events",
            "expirationDateTime": expires,
            "clientState": externalId,
        }
        headers = {
            "Authorization": "Bearer " + accessToken,
            "Content-Type": "application/json",
        }
        response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=body)
        if response.status_code == 401:
            newToken = self._refresh_access_token(extData, clientId, clientSecret)
            if newToken:
                extData["access_token"] = newToken
                headers["Authorization"] = "Bearer " + newToken
                response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=body)
        if response.status_code not in (200, 201):
            logEvent("ERROR", "webhook_subscription", "Outlook subscription registration failed",
                     userId=userId, details={"external_id": externalId, "status_code": response.status_code})
            raise RuntimeError("Outlook subscription registration failed")
        data = response.json()
        subscriptionId = data.get("id")
        subscriptionExpires = data.get("expirationDateTime") or expires
        self.updateSubscription(externalId, userId, subscriptionId, subscriptionExpires, None)
        self.stopSubscription(extData)
        logEvent("INFO", "webhook_subscription", "Outlook subscription registered",
                 userId=userId, details={"external_id": externalId, "subscription_id": subscriptionId})
        return data

    def stopSubscription(self, extData: dict) -> None:
        provider = (extData.get("provider") or "").lower()
        if provider == "google":
            self._stopGoogleSubscription(extData)
        elif provider == "outlook":
            self._stopOutlookSubscription(extData)

    def _stopGoogleSubscription(self, extData: dict) -> None:
        subscriptionId = extData.get("subscription_id")
        resourceId = extData.get("resource_id")
        accessToken = extData.get("access_token")
        if not subscriptionId or not resourceId or not accessToken:
            return
        headers = {
            "Authorization": "Bearer " + accessToken,
            "Content-Type": "application/json",
        }
        body = {
            "id": subscriptionId,
            "resourceId": resourceId,
        }
        response = requests.post("https://www.googleapis.com/calendar/v3/channels/stop", headers=headers, json=body)
        if response.status_code not in (200, 204):
            logEvent("WARNING", "webhook_subscription", "Google subscription stop failed",
                     userId=extData.get("user_id"),
                     details={"external_id": extData.get("id"), "status_code": response.status_code})

    def _stopOutlookSubscription(self, extData: dict) -> None:
        subscriptionId = extData.get("subscription_id")
        accessToken = extData.get("access_token")
        if not subscriptionId or not accessToken:
            return
        headers = {
            "Authorization": "Bearer " + accessToken,
        }
        url = "https://graph.microsoft.com/v1.0/subscriptions/" + subscriptionId
        response = requests.delete(url, headers=headers)
        if response.status_code not in (200, 202, 204, 404):
            logEvent("WARNING", "webhook_subscription", "Outlook subscription stop failed",
                     userId=extData.get("user_id"),
                     details={"external_id": extData.get("id"), "status_code": response.status_code})

    def pullWebhookData(self, externalId: str, googleClientId: str, googleClientSecret: str, outlookClientId: str, outlookClientSecret: str) -> Any:
        db = self.supabaseClient
        result = db.table("externals").select("*").eq("id", externalId).limit(1).execute()
        if not result.data:
            raise ValueError("External not found")
        extData = result.data[0]
        provider = (extData.get("provider") or "").lower()
        if provider == "google":
            clientId = googleClientId
            clientSecret = googleClientSecret
        elif provider == "outlook":
            clientId = outlookClientId
            clientSecret = outlookClientSecret
        else:
            raise ValueError("Provider does not support webhooks")
        worker = External(id=externalId, supabaseClient=db, userId=extData.get("user_id"))
        return worker.pullCalData(externalId, client_id=clientId, client_secret=clientSecret)
    
    def remove(self, externalId: str) -> Any:
        # delete this external connection, but only if it belongs to this user
        db = self.supabaseClient
        existing = db.table("externals").select("*").eq("id", externalId).eq("user_id", self.userId).execute()
        if not existing.data:
            raise ValueError("External not found or not owned by user")
        try:
            self.stopSubscription(existing.data[0])
        except Exception as err:
            logEvent("WARNING", "webhook_subscription", "Could not stop subscription before unlink",
                     userId=self.userId, details={"external_id": externalId, "error": str(err)})
        return db.table("externals").delete().eq("id", externalId).execute()

    def updateTokens(self, externalId: str, userId: str, accessToken: str = None, refreshToken: str = None) -> Any:
        db = self.supabaseClient
        updateData = {}
        if accessToken:
            updateData["access_token"] = accessToken
        if refreshToken:
            updateData["refresh_token"] = refreshToken
        if updateData:
            db.table("externals").update(updateData).eq("id", externalId).eq("user_id", userId).execute()

    def _refresh_access_token(self, ext_data: dict, client_id: str, client_secret: str) -> "str | None":
        provider = (ext_data.get("provider") or "").lower()
        refresh_token = ext_data.get("refresh_token")
        if not refresh_token or not client_id or not client_secret:
            return None
        if provider == "google":
            token_url = "https://oauth2.googleapis.com/token"
        elif provider == "outlook":
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        else:
            return None
        resp = requests.post(token_url, data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        })
        if resp.status_code != 200:
            logEvent("WARNING", "token_refresh_failed",
                     f"Token refresh failed for provider '{provider}'",
                     userId=ext_data.get("user_id"),
                     details={"external_id": ext_data.get("id"), "status_code": resp.status_code})
            return None
        new_tokens = resp.json()
        new_access_token = new_tokens.get("access_token")
        if not new_access_token:
            return None
        new_refresh_token = new_tokens.get("refresh_token") or None
        self.updateTokens(ext_data["id"], ext_data.get("user_id"), new_access_token, new_refresh_token)
        return new_access_token

    def pullCalData(self, externalId: str, client_id: str | None = None, client_secret: str | None = None) -> Any:
        # fetch events from the external provider and store them locally
        db = self.supabaseClient
        ext = db.table("externals").select("*").eq("id", externalId).single().execute()
        if not ext.data:
            return {"error": "External not found"}

        accessToken = ext.data.get("access_token")
        url = ext.data.get("url")
        userId = ext.data.get("user_id")
        provider = (ext.data.get("provider") or "").lower()

        if provider == "google":
            apiUrl = f"{url}/calendars/primary/events"
            headers = {"Authorization": f"Bearer {accessToken}"}
            resp = requests.get(apiUrl, headers=headers)
            if resp.status_code == 401:
                new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")
                if not new_token:
                    return {"error": "token_expired"}
                headers["Authorization"] = f"Bearer {new_token}"
                resp = requests.get(apiUrl, headers=headers)
            if resp.status_code != 200:
                return {"error": "Failed to fetch events"}
            events = resp.json().get("items", [])

            # find or create the synced calendar for this user
            cal = db.table("calendars").select("id").eq("owner_id", userId).eq("name", "Google Calendar (Synced)").execute()
            if cal.data:
                calId = cal.data[0]["id"]
            else:
                newCal = db.table("calendars").insert({"name": "Google Calendar (Synced)", "owner_id": userId, "member_ids": [userId], "events": []}).execute()
                calId = newCal.data[0]["id"]

            # build a row for each event and insert them all
            rows = []
            for e in events:
                start = e.get("start", {})
                end = e.get("end", {})
                row = {
                    "title": e.get("summary") or "Untitled Event",
                    "calendar_ids": [calId],
                    "owner_id": userId,
                    "start_timestamp": start.get("dateTime") or start.get("date"),
                    "end_timestamp": end.get("dateTime") or end.get("date"),
                }
                if e.get("description"):
                    row["description"] = e["description"]
                rows.append(row)
            db.table("events").delete().contains("calendar_ids", [calId]).execute()
            if rows:
                db.table("events").insert(rows).execute()
            return {"inserted": len(rows)}

        elif provider == "outlook":
            graphUrl = "https://graph.microsoft.com/v1.0/me/events"
            headers = {
                "Authorization": f"Bearer {accessToken}",
                "Prefer": 'outlook.body-content-type="text"',
            }
            params = {"$select": "subject,body,start,end", "$top": 100}

            events = []
            nextUrl = graphUrl
            refreshed = False
            while nextUrl:
                resp = requests.get(nextUrl, headers=headers, params=params if nextUrl == graphUrl else None)
                if resp.status_code == 401 and not refreshed:
                    new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")
                    if not new_token:
                        return {"error": "token_expired"}
                    headers["Authorization"] = f"Bearer {new_token}"
                    refreshed = True
                    resp = requests.get(nextUrl, headers=headers, params=params if nextUrl == graphUrl else None)
                if resp.status_code != 200:
                    return {"error": "Failed to fetch Outlook events"}
                data = resp.json()
                events.extend(data.get("value", []))
                nextUrl = data.get("@odata.nextLink")

            cal = db.table("calendars").select("id").eq("owner_id", userId).eq("name", "Outlook Calendar (Synced)").execute()
            if cal.data:
                calId = cal.data[0]["id"]
            else:
                newCal = db.table("calendars").insert({"name": "Outlook Calendar (Synced)", "owner_id": userId, "member_ids": [userId], "events": []}).execute()
                calId = newCal.data[0]["id"]

            rows = []
            for e in events:
                start = e.get("start", {})
                end = e.get("end", {})
                row = {
                    "title": e.get("subject") or "Untitled Event",
                    "calendar_ids": [calId],
                    "owner_id": userId,
                    "start_timestamp": start.get("dateTime"),
                    "end_timestamp": end.get("dateTime"),
                }
                body_content = (e.get("body") or {}).get("content", "").strip()
                if body_content:
                    row["description"] = body_content
                rows.append(row)
            db.table("events").delete().contains("calendar_ids", [calId]).execute()
            if rows:
                db.table("events").insert(rows).execute()
            return {"inserted": len(rows)}

        else:
            return {"error": f"Provider '{provider}' not supported"}

    def pushCalData(self, externalId: str, client_id: str | None = None, client_secret: str | None = None) -> Any:
        # push local events to the external provider
        db = self.supabaseClient
        ext = db.table("externals").select("*").eq("id", externalId).single().execute()
        if not ext.data:
            return {"error": "External not found"}

        accessToken = ext.data.get("access_token")
        url = ext.data.get("url")
        userId = ext.data.get("user_id")
        provider = (ext.data.get("provider") or "").lower()

        if provider == "google":
            # get all calendars this user owns except the synced one
            cals = db.table("calendars").select("id").eq("owner_id", userId).neq("name", "Google Calendar (Synced)").execute()
            calIds = [c["id"] for c in (cals.data or [])]
            if not calIds:
                return {"pushed": 0}

            apiUrl = f"{url}/calendars/primary/events"
            headers = {"Authorization": f"Bearer {accessToken}", "Content-Type": "application/json"}
            pushed = 0
            refreshed = False
            chunk_size = 200
            offset = 0
            while True:
                chunk = db.table("events").select("title, description, start_timestamp, end_timestamp, calendar_ids").overlaps("calendar_ids", calIds).range(offset, offset + chunk_size - 1).execute()
                localEvents = chunk.data or []
                for e in localEvents:
                    start = e.get("start_timestamp")
                    end = e.get("end_timestamp") or start
                    body = {
                        "summary": e.get("title") or "Untitled Event",
                        "start": {"dateTime": start},
                        "end": {"dateTime": end},
                    }
                    if e.get("description"):
                        body["description"] = e["description"]
                    resp = requests.post(apiUrl, headers=headers, json=body)
                    if resp.status_code == 401 and not refreshed:
                        new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")
                        if not new_token:
                            return {"error": "token_expired"}
                        headers["Authorization"] = f"Bearer {new_token}"
                        refreshed = True
                        resp = requests.post(apiUrl, headers=headers, json=body)
                    if resp.status_code in (200, 201):
                        pushed += 1
                if len(localEvents) < chunk_size:
                    break
                offset += chunk_size
            return {"pushed": pushed}

        elif provider == "outlook":
            cals = db.table("calendars").select("id").eq("owner_id", userId).neq("name", "Outlook Calendar (Synced)").execute()
            calIds = [c["id"] for c in (cals.data or [])]
            if not calIds:
                return {"pushed": 0}

            apiUrl = "https://graph.microsoft.com/v1.0/me/events"
            headers = {"Authorization": f"Bearer {accessToken}", "Content-Type": "application/json"}
            pushed = 0
            refreshed = False
            chunk_size = 200
            offset = 0
            while True:
                chunk = db.table("events").select("title, description, start_timestamp, end_timestamp, calendar_ids").overlaps("calendar_ids", calIds).range(offset, offset + chunk_size - 1).execute()
                localEvents = chunk.data or []
                for e in localEvents:
                    start = e.get("start_timestamp")
                    end = e.get("end_timestamp") or start
                    body = {
                        "subject": e.get("title") or "Untitled Event",
                        "body": {"contentType": "text", "content": e.get("description") or ""},
                        "start": {"dateTime": start, "timeZone": "UTC"},
                        "end": {"dateTime": end, "timeZone": "UTC"},
                    }
                    resp = requests.post(apiUrl, headers=headers, json=body)
                    if resp.status_code == 401 and not refreshed:
                        new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")
                        if not new_token:
                            return {"error": "token_expired"}
                        headers["Authorization"] = f"Bearer {new_token}"
                        refreshed = True
                        resp = requests.post(apiUrl, headers=headers, json=body)
                    if resp.status_code in (200, 201):
                        pushed += 1
                if len(localEvents) < chunk_size:
                    break
                offset += chunk_size
            return {"pushed": pushed}

        else:
            return {"error": f"Provider '{provider}' not supported"}
