from typing import Any


class Event:
    def __init__(
        self,
        title: str,
        supabaseClient: Any,
        calendarIds: list[str],
        ownerId: str | None = None,
        description: str | None = None,
        startTimestamp: str | None = None,
        endTimestamp: str | None = None,
    ) -> None:
        self.id: str | None = None
        self.supabaseClient = supabaseClient
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
        # insert this event into the database
        return self.supabaseClient.table("events").insert(self.to_record()).execute()

    def remove(self) -> Any:
        # delete this event from the database
        if self.id is None:
            raise ValueError("Event must be saved before it can be removed")
        return self.supabaseClient.table("events").delete().match({"id": self.id}).execute()

    def edit(self, title=None, description=None, startTimestamp=None, endTimestamp=None, calendarIds=None) -> Any:
        # update one or more fields on this event
        if self.id is None:
            raise ValueError("Event must be saved before it can be edited")
        recordData = self.to_record()
        if title is not None:
            recordData["title"] = title
        if description is not None:
            recordData["description"] = description
        if startTimestamp is not None:
            recordData["start_timestamp"] = startTimestamp
        if endTimestamp is not None:
            recordData["end_timestamp"] = endTimestamp
        if calendarIds is not None:
            recordData["calendar_ids"] = calendarIds
        return self.supabaseClient.table("events").update(recordData).match({"id": self.id}).execute()
