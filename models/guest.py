from utils.supabase_client import get_supabase_client
from typing import Any


class Guest:
    # Guest users access the app through a guest link, no login required

    def viewCalendar(self, calendarId: str) -> Any:
        # look up a calendar by id and return it
        db = get_supabase_client()
        result = db.table("calendars").select("*").eq("id", calendarId).execute()
        return result.data

    def viewEvent(self, eventId: str) -> Any:
        # look up a single event by id and return it
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", eventId).execute()
        return result.data

    def editCalendar(self, calendarId: str, name: str) -> Any:
        # guests with edit access can update the calendar name
        db = get_supabase_client()
        result = db.table("calendars").update({"name": name}).eq("id", calendarId).execute()
        return result.data

    def editEvent(self, eventId: str, title: str | None = None, description: str | None = None, startTimestamp: str | None = None, endTimestamp: str | None = None) -> Any:
        # guests with edit access can update event fields
        db = get_supabase_client()
        # build the update dict with only the fields that were actually given
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if startTimestamp is not None:
            updates["start_timestamp"] = startTimestamp
        if endTimestamp is not None:
            updates["end_timestamp"] = endTimestamp
        if len(updates) == 0:
            return []
        result = db.table("events").update(updates).eq("id", eventId).execute()
        return result.data
