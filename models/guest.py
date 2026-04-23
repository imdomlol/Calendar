from utils.supabase_client import get_supabase_client
from typing import Any


class Guest:
    # Guest does not need to be logged in
    # they access the app through a guest link, so no userId is required

    def viewCalendar(self, calendar_id: str) -> Any:
        # look up a calendar by id and return it
        db = get_supabase_client()
        result = db.table("calendars").select("*").eq("id", calendar_id).execute()
        return result.data

    def viewEvent(self, event_id: str) -> Any:
        # look up a single event by id and return it
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", event_id).execute()
        return result.data

    def editCalendar(self, calendar_id: str, name: str) -> Any:
        # guests with edit access can update the calendar name
        db = get_supabase_client()
        result = db.table("calendars").update({"name": name}).eq("id", calendar_id).execute()
        return result.data

    def editEvent(self, event_id: str, title: str | None = None, description: str | None = None, start_timestamp: str | None = None, end_timestamp: str | None = None) -> Any:
        # guests with edit access can update event fields
        db = get_supabase_client()
        # only include fields that were actually passed in
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if start_timestamp is not None:
            updates["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            updates["end_timestamp"] = end_timestamp
        if len(updates) == 0:
            return []
        result = db.table("events").update(updates).eq("id", event_id).execute()
        return result.data
