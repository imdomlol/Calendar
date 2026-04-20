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
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "calendar_ids": self.calendar_ids,
            "title": self.title,
            "description": self.description,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "age_timestamp": self.age_timestamp,
        }

    def save(self) -> Any:
        return self.supabase_client.table("events").insert(self.to_record()).execute()

    def remove(self) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before removed.")
        return self.supabase_client.table("events").delete().match({"id": self.id}).execute()

    def edit(self, **kwargs: Any) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before edited.")
        data = self.to_record()
        for key, value in kwargs.items():
            if key in data:
                data[key] = value
        return self.supabase_client.table("events").update(data).match({"id": self.id}).execute()
