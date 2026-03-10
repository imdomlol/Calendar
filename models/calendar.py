from typing import Any


class Calendar:
    def __init__(self, name: str, owner_id: str) -> None:
        self.id = None # Will be set when the calendar is saved to the database
        self.name = name
        self.owner_id = owner_id
        self.member_ids: list[str] = [owner_id]
        self.events: list[str] = []
        self.age_timestamp = None # Will be set when the calendar is saved to the database

    def add_event(self, event_id: str) -> None:
        self.events.append(event_id)

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "member_ids": self.member_ids,
            "events": self.events,
            "age_timestamp": self.age_timestamp,
        }

    def save(self) -> Any:
        from utils.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        return supabase.table("calendars").insert(self.to_record()).execute()
