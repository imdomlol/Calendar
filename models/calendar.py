from utils.supabase_client import get_supabase_client
from typing import Any


class Calendar:
    def __init__(self, name: str, owner_id: str) -> None:
        # id is None until we save to the database
        # the database generates the id for us
        self.id: str | None = None
        self.name = name
        self.owner_id = owner_id
        # owner starts as a member so we put them in the list first
        memberList = [owner_id]
        self.member_ids: list[str] = memberList
        self.events: list[str] = []
        # age_timestamp gets set by supabase on insert
        self.age_timestamp: str | None = None


    def add_event(self, event_id: str) -> None:
        self.events.append(event_id)

    def to_record(self) -> dict[str, Any]:
        # build the dict to insert into supabase
        # keys need to match the column names in the calendars table
        rec = {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "member_ids": self.member_ids,
            "events": self.events,
            "age_timestamp": self.age_timestamp,
        }
        return rec


    def save(self) -> Any:
        db = get_supabase_client()
        return db.table("calendars").insert(self.to_record()).execute()

    def remove_calendar(self) -> Any:
        sb = get_supabase_client()
        return sb.table("calendars").delete().eq("id", self.id).execute()
