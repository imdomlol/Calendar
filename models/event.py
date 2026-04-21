from typing import Any


class Event:
    def __init__(
        self,
        title: str,
        supabase_client: Any,
        calendar_ids: list[str],
        owner_id: str | None = None,
        description: str | None = None,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
    ) -> None:
        self.id: str | None = None
        self.supabase_client = supabase_client
        self.owner_id = owner_id
        self.title = title
        self.calendar_ids = calendar_ids
        self.description = description
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.age_timestamp: str | None = None

    def to_record(self) -> dict[str, Any]:
        # turn the event into a dict for inserting into the database
        # all the keys need to match the column names in the events table
        # we build the whole thing then return it
        rec = {
            "id": self.id,
            "owner_id": self.owner_id,
            "calendar_ids": self.calendar_ids,
            "title": self.title,
            "description": self.description,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "age_timestamp": self.age_timestamp,
        }
        # return the dict to whoever asked for it
        return rec


    def save(self) -> Any:
        return self.supabase_client.table("events").insert(self.to_record()).execute()

    def remove(self) -> Any:
        idMissing = self.id is None
        if idMissing == True:
            raise ValueError("Event must be saved before removed.")
        return self.supabase_client.table("events").delete().match({"id": self.id}).execute()


    def edit(self, title=None, description=None, start_timestamp=None, end_timestamp=None, calendar_ids=None) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before edited.")
        recordData = self.to_record()
        if title is not None:
            recordData["title"] = title
        if description is not None:
            recordData["description"] = description
        if start_timestamp is not None:
            recordData["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            recordData["end_timestamp"] = end_timestamp
        if calendar_ids is not None:
            recordData["calendar_ids"] = calendar_ids
        return self.supabase_client.table("events").update(recordData).match({"id": self.id}).execute()
