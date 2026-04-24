from utils.supabase_client import get_supabase_client
from typing import Any


class Guest:
    # Guest users access the app through a guest link, no login required

    @staticmethod
    def viewCalendar(calendarId: str) -> Any:
        db = get_supabase_client()
        result = db.table("calendars").select("*").eq("id", calendarId).execute()
        return result.data

    @staticmethod
    def viewEvent(eventId: str) -> Any:
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", eventId).execute()
        return result.data

    @staticmethod
    def editCalendar(calendarId: str, name: str) -> Any:
        db = get_supabase_client()
        result = db.table("calendars").update({"name": name}).eq("id", calendarId).execute()
        return result.data

    @staticmethod
    def editEvent(eventId: str, title: str | None = None, description: str | None = None, startTimestamp: str | None = None, endTimestamp: str | None = None) -> Any:
        db = get_supabase_client()
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
        return result.data or []
