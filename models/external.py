from datetime import datetime, timedelta, timezone
import requests
from typing import Any
from uuid import uuid4
from utils.logger import log_event


# ========================= External Model =========================

# this class represents a connection to an external calendar provider
# it handles saving connections, syncing events, and managing webhook subscriptions
# supported providers are Google Calendar and Outlook

class External:
    # stores the database client and which user owns this connection
    def __init__(
        self,
        id: str | None,
        supabaseClient: Any,
        userId: str,
    ) -> None:
        self.id = id
        self.userId = userId
        self.supabaseClient = supabaseClient


    # ========================= Saving and Finding =========================

    # this saves a new external connection record to the database
    def save(self, url: str, provider: str, accessToken: str | None = None, refreshToken: str | None = None) -> Any:
        # build the dict we want to insert into the externals table
        record = {
            "url": url,
            "provider": provider,
            "user_id": self.userId,
            "access_token": accessToken,
            "refresh_token": refreshToken,
        }
        
        # supabase generates an id for us but if we want custom ids include here
        if self.id is not None:
            record["id"] = self.id

        return self.supabaseClient.table("externals").insert(record).execute()

    # this looks up an existing external connection for the current user
    def find_for_user_provider(self, provider: str, url: str):
        db = self.supabaseClient

        # query for a row that belongs to this user and matches provider and url
        result = db.table("externals").select("*").eq("user_id", self.userId).eq("provider", provider).eq("url", url).limit(1).execute()

        if result.data:
            return result.data[0]
        
        return None

    # ========================= Subscription Management =========================

    # this writes webhook subscription info back to an externals row
    def update_subscription(self, externalId: str, userId: str, subscriptionId: str | None, subscriptionExpires: str | None, resourceId: str | None = None) -> Any:
        db = self.supabaseClient

        updateData = {}
        updateData["subscription_id"] = subscriptionId
        updateData["subscription_expires"] = subscriptionExpires
        updateData["resource_id"] = resourceId

        return db.table("externals").update(updateData).eq("id", externalId).eq("user_id", userId).execute()

    # this builds the webhook notification url our server will receive events at
    # Google uses one path and Outlook uses another
    def _subscription_url(self, appBaseUrl: str, provider: str) -> str:
        # strip trailing slashes so we do not end up with double slashes
        cleanBaseUrl = appBaseUrl.strip().rstrip("/")

        if provider == "google":
            return cleanBaseUrl + "/api/webhooks/google"
        
        return cleanBaseUrl + "/api/webhooks/outlook"

    # this registers a new webhook subscription with the external calendar provider
    def register_subscription(self, externalId: str, appBaseUrl: str, clientId: str = "", clientSecret: str = "") -> Any:
        db = self.supabaseClient

        # look up the external
        result = db.table("externals").select("*").eq("id", externalId).eq("user_id", self.userId).limit(1).execute()

        if not result.data:
            raise ValueError("External not found or not owned by user")
        
        extData = result.data[0]

        # set provider name to lowercase so comparisons are easy
        provider = extData.get("provider") or ""
        provider = provider.lower()

        if provider == "google":
            return self._register_google_subscription(extData, appBaseUrl, clientId, clientSecret)
        
        if provider == "outlook":
            return self._register_outlook_subscription(extData, appBaseUrl, clientId, clientSecret)
        
        raise ValueError("Provider does not support webhooks")

    # this sends a "watch request" to the Google Calendar API to start receiving webhooks
    # it generates a unique channel id for this subscription
    # if the token is expired it tries to refresh once before failing
    def _register_google_subscription(self, extData: dict, appBaseUrl: str, clientId: str, clientSecret: str) -> Any:
        accessToken = extData.get("access_token")
        externalId = extData.get("id")
        userId = extData.get("user_id")

        # generate a unique id for this notification channel
        channelId = str(uuid4())
        address = self._subscription_url(appBaseUrl, "google")

        # build the request body in the Google server format
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

        # send the subscription request to Google
        response = requests.post(url, headers=headers, json=body)

        # 401 means the token is expired so we try to refresh it once
        if response.status_code == 401:
            newToken = self._refresh_access_token(extData, clientId, clientSecret)

            if newToken:
                extData["access_token"] = newToken
                headers["Authorization"] = "Bearer " + newToken
                response = requests.post(url, headers=headers, json=body)

        if response.status_code not in (200, 201):
            log_event(
                "ERROR", 
                "webhook_subscription", 
                "Google subscription registration failed",
                userId=userId, 
                details={
                    "external_id": externalId, 
                    "status_code": response.status_code
                }
            )
            
            raise RuntimeError("Google subscription registration failed")
        
        data = response.json()

        # Google returns expiration as "milliseconds since epoch" so we convert it
        expires = None
        expiration = data.get("expiration")

        if expiration:
            expiresAt = datetime.fromtimestamp(int(expiration) / 1000, timezone.utc)
            expires = expiresAt.isoformat()

        subscriptionId = data.get("id")
        resourceId = data.get("resourceId")

        # save the new subscription details to the database
        self.update_subscription(externalId, userId, subscriptionId, expires, resourceId)

        # stop the old subscription if one was already running
        self.stop_subscription(extData)

        log_event(
            "INFO", 
            "webhook_subscription", 
            "Google subscription registered",
            userId=userId, 
            details={
                "external_id": externalId, 
                "subscription_id": subscriptionId
            }
        )
        
        return data

    # this sends a "subscription request" to the Microsoft Graph API for Outlook webhooks
    # if the token is expired it tries to refresh once before failing
    def _register_outlook_subscription(self, extData: dict, appBaseUrl: str, clientId: str, clientSecret: str) -> Any:
        accessToken = extData.get("access_token")
        externalId = extData.get("id")
        userId = extData.get("user_id")
        
        # Microsoft limits subscriptions to just under 3 days so we set 2 days 23 hours
        expiresAt = datetime.now(timezone.utc) + timedelta(days=2, hours=23)

        # Microsoft expects the time in "Z format"
        isoStr = expiresAt.isoformat()
        expires = isoStr.replace("+00:00", "Z")
        address = self._subscription_url(appBaseUrl, "outlook")

        # build the request body in the Microsoft Graph format
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

        # send the subscription request to Microsoft Graph
        response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=body)

        # refresh token once same as google
        if response.status_code == 401:
            newToken = self._refresh_access_token(extData, clientId, clientSecret)

            if newToken:
                extData["access_token"] = newToken
                headers["Authorization"] = "Bearer " + newToken
                response = requests.post("https://graph.microsoft.com/v1.0/subscriptions", headers=headers, json=body)

        if response.status_code not in (200, 201):
            log_event(
                "ERROR", 
                "webhook_subscription", 
                "Outlook subscription registration failed",
                userId=userId, 
                details={
                    "external_id": externalId, 
                    "status_code": response.status_code
                }
            )

            raise RuntimeError("Outlook subscription registration failed")
        
        data = response.json()
        subscriptionId = data.get("id")

        # use the expiry from the response if they give it to us, otherwise what we calculated
        subscriptionExpires = data.get("expirationDateTime") or expires

        # save the new subscription details to the database
        self.update_subscription(externalId, userId, subscriptionId, subscriptionExpires, None)

        # stop the old subscription if one was already running
        self.stop_subscription(extData)

        log_event(
            "INFO", 
            "webhook_subscription", 
            "Outlook subscription registered",
            userId=userId, 
            details={
                "external_id": externalId, 
                "subscription_id": subscriptionId
            }
        )

        return data

    # this stops a webhook subscription
    def stop_subscription(self, extData: dict) -> None:
        # set provider name to lowercase for comparing
        provider = extData.get("provider") or ""
        provider = provider.lower()

        if provider == "google":
            self._stop_google_subscription(extData)
        elif provider == "outlook":
            self._stop_outlook_subscription(extData)

    # this cancels an active Google webhook channel
    def _stop_google_subscription(self, extData: dict) -> None:
        subscriptionId = extData.get("subscription_id")
        resourceId = extData.get("resource_id")
        accessToken = extData.get("access_token")

        # we need all three vars to send the stop request
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

        # ask Google to stop sending notifications for this channel
        response = requests.post("https://www.googleapis.com/calendar/v3/channels/stop", headers=headers, json=body)

        if response.status_code not in (200, 204):
            log_event(
                "WARNING", 
                "webhook_subscription", 
                "Google subscription stop failed",
                userId=extData.get("user_id"),
                details={
                    "external_id": extData.get("id"), 
                    "status_code": response.status_code
                }
            )

    # this deletes an active Outlook subscription
    def _stop_outlook_subscription(self, extData: dict) -> None:
        subscriptionId = extData.get("subscription_id")
        accessToken = extData.get("access_token")

        # we need both variables to send the delete request
        if not subscriptionId or not accessToken:
            return
        
        headers = {
            "Authorization": "Bearer " + accessToken,
        }

        url = "https://graph.microsoft.com/v1.0/subscriptions/" + subscriptionId

        # ask Microsoft to delete this subscription
        response = requests.delete(url, headers=headers)
        if response.status_code not in (200, 202, 204, 404):
            log_event(
                "WARNING", 
                "webhook_subscription", 
                "Outlook subscription stop failed",
                userId=extData.get("user_id"),
                details={
                    "external_id": extData.get("id"), 
                    "status_code": response.status_code
                }
            )


    # ========================= Webhook Data =========================

    # this is called when a notification arrives for this external
    def pull_webhook_data(self, externalId: str, googleClientId: str, googleClientSecret: str, outlookClientId: str, outlookClientSecret: str) -> Any:
        db = self.supabaseClient
        result = db.table("externals").select("*").eq("id", externalId).limit(1).execute()

        if not result.data:
            raise ValueError("External not found")
        
        extData = result.data[0]

        # adjust provider name to lowercase to compare
        provider = extData.get("provider") or ""
        provider = provider.lower()

        # pick the ids that match
        if provider == "google":
            clientId = googleClientId
            clientSecret = googleClientSecret
        elif provider == "outlook":
            clientId = outlookClientId
            clientSecret = outlookClientSecret
        else:
            raise ValueError("Provider does not support webhooks")
        
        # create a fresh External object and call pull_cal_data to sync events
        worker = External(id=externalId, supabaseClient=db, userId=extData.get("user_id"))

        return worker.pull_cal_data(externalId, client_id=clientId, client_secret=clientSecret)


    # ========================= CRUD Helpers =========================

    # this deletes an external connection from the database
    def remove(self, externalId: str) -> Any:
        db = self.supabaseClient
        existing = db.table("externals").select("*").eq("id", externalId).eq("user_id", self.userId).execute()

        if not existing.data:
            raise ValueError("External not found or not owned by user")
        
        # try to stop the subscription before deleting
        # if stopping fails we still want to delete
        try:
            self.stop_subscription(existing.data[0])
        except Exception as err:
            log_event(
                "WARNING", 
                "webhook_subscription", 
                "Could not stop subscription before unlink",
                userId=self.userId, 
                details={
                    "external_id": externalId, 
                    "error": str(err)
                }
            )

        return db.table("externals").delete().eq("id", externalId).execute()

    # this updates the stored oauth tokens for an external connection in the database
    # it only updates fields that were actually given
    # always called after a token refresh to save the new tokens
    def update_tokens(self, externalId: str, userId: str, accessToken: str = None, refreshToken: str = None) -> Any:
        db = self.supabaseClient
        updateData = {}

        # only include a field if a value was actually provided
        if accessToken:
            updateData["access_token"] = accessToken

        if refreshToken:
            updateData["refresh_token"] = refreshToken

        if updateData:
            db.table("externals").update(updateData).eq("id", externalId).eq("user_id", userId).execute()


    # ========================= Token Refresh =========================

    # this tries to get a new access token using the stored refresh token
    def _refresh_access_token(self, ext_data: dict, client_id: str, client_secret: str) -> "str | None":
        # change provider name to lowercase (standard)
        provider = ext_data.get("provider") or ""
        provider = provider.lower()
        refresh_token = ext_data.get("refresh_token")

        # we need all three for a token refresh
        if not refresh_token or not client_id or not client_secret:
            return None
        
        # pick the link for the provider
        if provider == "google":
            token_url = "https://oauth2.googleapis.com/token"
        elif provider == "outlook":
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        else:
            return None
        
        # send the refresh request to the link
        resp = requests.post(
            token_url, 
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            }
        )

        if resp.status_code != 200:
            log_event(
                "WARNING", 
                "token_refresh_failed",
                f"Token refresh failed for provider '{provider}'",
                userId=ext_data.get("user_id"),
                details={
                    "external_id": ext_data.get("id"), 
                    "status_code": resp.status_code
                }
            )

            return None
        
        new_tokens = resp.json()
        new_access_token = new_tokens.get("access_token")

        if not new_access_token:
            return None
        
        # some providers return a new refresh token and some do not
        new_refresh_token = new_tokens.get("refresh_token") or None

        # save the new tokens back to the database so they are used next time
        self.update_tokens(ext_data["id"], ext_data.get("user_id"), new_access_token, new_refresh_token)

        return new_access_token


    # ========================= Pull and Push =========================

    # this fetches events from the external calendar provider and saves them in supabase
    def pull_cal_data(self, externalId: str, client_id: str | None = None, client_secret: str | None = None) -> Any:
        db = self.supabaseClient

        # look up external so we have the provider and tokens
        ext = db.table("externals").select("*").eq("id", externalId).single().execute()

        if not ext.data:
            return {"error": "External not found"}

        accessToken = ext.data.get("access_token")
        url = ext.data.get("url")
        userId = ext.data.get("user_id")

        # compare lowered names
        provider = ext.data.get("provider") or ""
        provider = provider.lower()

        if provider == "google":
            # build the url for the Google cal
            apiUrl = f"{url}/calendars/primary/events"
            headers = {"Authorization": f"Bearer {accessToken}"}
            resp = requests.get(apiUrl, headers=headers)

            # try to refresh it once
            if resp.status_code == 401:
                new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")

                if not new_token:
                    return {"error": "token_expired"}
                
                headers["Authorization"] = f"Bearer {new_token}"
                resp = requests.get(apiUrl, headers=headers)

            if resp.status_code != 200:
                return {"error": "Failed to fetch events"}
            
            events = resp.json().get("items", [])

            # find or create the synced calendar
            cal = db.table("calendars").select("id").eq("owner_id", userId).eq("name", "Google Calendar (Synced)").execute()

            if cal.data:
                calId = cal.data[0]["id"]
            else:
                newCal = db.table("calendars").insert({"name": "Google Calendar (Synced)", "owner_id": userId, "member_ids": [userId], "events": []}).execute()
                calId = newCal.data[0]["id"]

            # build a row dict for each event
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

            # delete all previously synced events before inserting fresh ones
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

            # this stops us from trying to refresh the token more than once per pull
            refreshed = False

            # Outlook gives results by pages so we loop until there is no nextLink
            while nextUrl:
                resp = requests.get(nextUrl, headers=headers, params=params if nextUrl == graphUrl else None)

                # 401 means the token is expired so refresh
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

                # if there is a nextLink the API has more pages for us to fetch
                nextUrl = data.get("@odata.nextLink")

            # find synced calendar same as google
            cal = db.table("calendars").select("id").eq("owner_id", userId).eq("name", "Outlook Calendar (Synced)").execute()

            if cal.data:
                calId = cal.data[0]["id"]
            else:
                newCal = db.table("calendars").insert({"name": "Outlook Calendar (Synced)", "owner_id": userId, "member_ids": [userId], "events": []}).execute()
                calId = newCal.data[0]["id"]

            # build a row dict for each event so we can insert them all at once same as google
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

                # the body content is inside a body object
                bodyObj = e.get("body") or {}
                body_content = bodyObj.get("content", "")
                body_content = body_content.strip()

                if body_content:
                    row["description"] = body_content

                rows.append(row)

            # delete previous events
            db.table("events").delete().contains("calendar_ids", [calId]).execute()

            if rows:
                db.table("events").insert(rows).execute()

            return {"inserted": len(rows)}

        else:
            return {"error": f"Provider '{provider}' not supported"}

    # this pushes local events from this app out to the external calendar provider
    # it includes synced calendars, so imported events can be pushed back for now
    def push_cal_data(self, externalId: str, client_id: str | None = None, client_secret: str | None = None) -> Any:
        db = self.supabaseClient

        # look up external
        ext = db.table("externals").select("*").eq("id", externalId).single().execute()

        if not ext.data:
            return {"error": "External not found"}

        accessToken = ext.data.get("access_token")
        url = ext.data.get("url")
        userId = ext.data.get("user_id")

        # fix name to lower
        provider = ext.data.get("provider") or ""
        provider = provider.lower()

        if provider == "google":
            cals = db.table("calendars").select("id").eq("owner_id", userId).execute()

            # build the list of calendar ids we want to push events from
            calIds = []
            for c in (cals.data or []):
                calIds.append(c["id"])
            if not calIds:
                return {"pushed": 0}

            # build the url for the Google Calendar events
            apiUrl = f"{url}/calendars/primary/events"
            headers = {"Authorization": f"Bearer {accessToken}", "Content-Type": "application/json"}
            pushed = 0
            refreshed = False
            chunk_size = 200
            offset = 0

            # loop through events in chunks for memory 
            while True:
                chunk = db.table("events").select("title, description, start_timestamp, end_timestamp, calendar_ids").overlaps("calendar_ids", calIds).range(offset, offset + chunk_size - 1).execute()
                localEvents = chunk.data or []

                for e in localEvents:
                    start = e.get("start_timestamp")

                    # fall back to start time if end is missing
                    end = e.get("end_timestamp") or start
                    body = {
                        "summary": e.get("title") or "Untitled Event",
                        "start": {"dateTime": start},
                        "end": {"dateTime": end},
                    }

                    if e.get("description"):
                        body["description"] = e["description"]

                    resp = requests.post(apiUrl, headers=headers, json=body)

                    # 401 on the first attempt means the token is expired so we try refreshing
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
                    # we have reached the end
                    break

                offset += chunk_size

            return {"pushed": pushed}

        elif provider == "outlook":
            cals = db.table("calendars").select("id").eq("owner_id", userId).execute()

            # build list of calendar ids
            calIds = []
            for c in (cals.data or []):
                calIds.append(c["id"])
            if not calIds:
                return {"pushed": 0}

            apiUrl = "https://graph.microsoft.com/v1.0/me/events"
            headers = {"Authorization": f"Bearer {accessToken}", "Content-Type": "application/json"}
            pushed = 0
            refreshed = False
            chunk_size = 200
            offset = 0

            # loop events in chunks
            while True:
                chunk = db.table("events").select("title, description, start_timestamp, end_timestamp, calendar_ids").overlaps("calendar_ids", calIds).range(offset, offset + chunk_size - 1).execute()
                localEvents = chunk.data or []

                for e in localEvents:
                    start = e.get("start_timestamp")

                    # fall back to start time if end is missing
                    end = e.get("end_timestamp") or start
                    body = {
                        "subject": e.get("title") or "Untitled Event",
                        "body": {"contentType": "text", "content": e.get("description") or ""},
                        "start": {"dateTime": start, "timeZone": "UTC"},
                        "end": {"dateTime": end, "timeZone": "UTC"},
                    }

                    resp = requests.post(apiUrl, headers=headers, json=body)

                    # try refreshing on 401
                    if resp.status_code == 401 and not refreshed:
                        new_token = self._refresh_access_token(ext.data, client_id or "", client_secret or "")

                        if not new_token:
                            return {"error": "token_expired"}
                        
                        headers["Authorization"] = f"Bearer {new_token}"
                        refreshed = True
                        resp = requests.post(apiUrl, headers=headers, json=body)

                    if resp.status_code in (200, 201):
                        pushed += 1

                # we have reached the end
                if len(localEvents) < chunk_size:
                    break

                offset += chunk_size
                
            return {"pushed": pushed}

        else:
            return {"error": f"Provider '{provider}' not supported"}
