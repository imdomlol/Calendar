import requests
from typing import Any


class External:
    def __init__(
        self,
        id: str | None,
        url: str,
        provider: str,
        supabaseClient: Any,
        userId: str | None = None,
        accessToken: str | None = None,
        refreshToken: str | None = None,
    ) -> None:
        self.id = id
        self.url = url
        self.provider = provider
        self.userId = userId
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.supabaseClient = supabaseClient

    def to_record(self) -> dict[str, Any]:
        # build a dict with column names matching the externals table in supabase
        rec = {
            "id": self.id,
            "url": self.url,
            "provider": self.provider,
            "user_id": self.userId,
            "access_token": self.accessToken,
            "refresh_token": self.refreshToken,
        }
        return rec

    def save(self) -> Any:
        # insert this external connection into the database
        record = self.to_record()
        return self.supabaseClient.table("externals").insert(record).execute()

    def updateTokens(self, externalId: str, userId: str, accessToken: str = None, refreshToken: str = None) -> Any:
        db = self.supabaseClient
        updateData = {}
        if accessToken:
            updateData["access_token"] = accessToken
        if refreshToken:
            updateData["refresh_token"] = refreshToken
        if updateData:
            db.table("externals").update(updateData).eq("id", externalId).eq("user_id", userId).execute()

    def remove(self, externalId: str) -> Any:
        # delete this external connection, but only if it belongs to this user
        db = self.supabaseClient
        existing = db.table("externals").select("id").eq("id", externalId).eq("user_id", self.userId).execute()
        if not existing.data:
            raise ValueError("External not found or not owned by user")
        return db.table("externals").delete().eq("id", externalId).execute()

    def pullCalData(self, externalId: str) -> Any:
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
            if rows:
                db.table("events").insert(rows).execute()
            return {"inserted": len(rows)}

        elif provider == "outlook":
            return {"error": "Outlook sync not implemented yet"}
        else:
            return {"error": f"Provider '{provider}' not supported"}

    def pushCalData(self, externalId: str) -> Any:
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
                    if resp.status_code in (200, 201):
                        pushed += 1
                if len(localEvents) < chunk_size:
                    break
                offset += chunk_size
            return {"pushed": pushed}

        elif provider == "outlook":
            return {"error": "Outlook push not implemented yet"}
        else:
            return {"error": f"Provider '{provider}' not supported"}
