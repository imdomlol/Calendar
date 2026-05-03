from utils.supabase_client import get_supabase_client
from typing import Any


class Event:
    def __init__(
        self,
        title: str,
        calendarIds: list[str],
        ownerId: str | None = None,
        description: str | None = None,
        startTimestamp: str | None = None,
        endTimestamp: str | None = None,
    ) -> None:
        self.id: str | None = None
        self.ownerId = ownerId
        self.title = title
        self.calendarIds = calendarIds
        self.description = description
        self.startTimestamp = startTimestamp
        self.endTimestamp = endTimestamp
        self.ageTimestamp: str | None = None

    def to_record(self) -> dict[str, Any]:
        rec = {
            "owner_id": self.ownerId,
            "calendar_ids": self.calendarIds,
            "title": self.title,
            "description": self.description,
            "start_timestamp": self.startTimestamp,
            "end_timestamp": self.endTimestamp,
        }
        if self.id is not None:
            rec["id"] = self.id
        if self.ageTimestamp is not None:
            rec["age_timestamp"] = self.ageTimestamp
        return rec

    def save(self) -> Any:
        db = get_supabase_client()
        result = db.table("events").insert(self.to_record()).execute()
        rows = result.data or []

        if rows:
            newId = rows[0].get("id")
            self.id = newId

            try:
                Event._addEventToCalendars(newId, self.calendarIds or [])
            except Exception:
                # Event lookup uses events.calendar_ids. The calendars.events list is
                # only a cached count/display helper, so don't fail a successful insert
                # if that denormalized backfill is blocked or stale.
                pass

        return result

    def remove(self) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before it can be removed")
        db = get_supabase_client()
        result = db.table("events").delete().match({"id": self.id}).execute()
        Event._removeEventFromCalendars(self.id, self.calendarIds or [])
        return result

    @staticmethod
    def _addEventToCalendars(eventId, calIds) -> None:
        if not eventId or not calIds:
            return
        
        db = get_supabase_client()
        for calId in calIds:
            row = db.table("calendars").select("events").eq("id", calId).limit(1).execute()
            if not row.data:
                continue
            current = row.data[0].get("events") or []
            if eventId not in current:
                current.append(eventId)
                db.table("calendars").update({"events": current}).eq("id", calId).execute()

    @staticmethod
    def _removeEventFromCalendars(eventId, calIds) -> None:
        if not eventId or not calIds:
            return
        db = get_supabase_client()
        for calId in calIds:
            row = db.table("calendars").select("events").eq("id", calId).limit(1).execute()
            if not row.data:
                continue
            current = row.data[0].get("events") or []
            if eventId in current:
                current.remove(eventId)
                db.table("calendars").update({"events": current}).eq("id", calId).execute()

    @staticmethod
    def find(eventId: str) -> dict | None:
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", eventId).limit(1).execute()
        rows = result.data or []
        if rows:
            return rows[0]
        return None

    def edit(self, title=None, description=None, startTimestamp=None, endTimestamp=None, calendarIds=None) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before it can be edited")
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if startTimestamp is not None:
            updates["start_timestamp"] = startTimestamp
        if endTimestamp is not None:
            updates["end_timestamp"] = endTimestamp
        if calendarIds is not None:
            updates["calendar_ids"] = calendarIds
        db = get_supabase_client()
        result = db.table("events").update(updates).match({"id": self.id}).execute()
        if calendarIds is not None:
            oldIds = self.calendarIds or []
            newIds = calendarIds or []
            toAdd = [c for c in newIds if c not in oldIds]
            toRemove = [c for c in oldIds if c not in newIds]
            Event._addEventToCalendars(self.id, toAdd)
            Event._removeEventFromCalendars(self.id, toRemove)
            self.calendarIds = newIds
        return result
