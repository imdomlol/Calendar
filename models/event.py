from typing import Any

class Event:
    def __init__(self, title: str, supabase_client: Any, calendar_ids: list, description: str = None, start_timestamp: str = None, end_timestamp: str = None,) -> None:
        self.id = None  # Will be set when the event is saved to the database
        self.supabase_client = supabase_client
        self.title = title
        self.calendar_ids = calendar_ids
        self.description = description
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.age_timestamp = None  # May be returned by DB on insert

    def to_record(self) -> dict:
        return {
            "id": self.id,
            "calendar_ids": self.calendar_ids,
            "title": self.title,
            "description": self.description,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "age_timestamp": self.age_timestamp,
        }

    def save(self) -> Any:
        record = self.to_record()
        result = self.supabase_client.table("events").insert(record).execute()

        return result
        
    def remove(self) -> Any:
		if self.id is None:
			raise ValueError("Event must be saved before removed.")
			
		result = self.supabase_client.table("events").delete().match({"id":self.id}).execute()
		return result
		
	def edit(self, **kwargs) -> Any:
		if self.id is None:
			raise ValueError("Event must be saved before edited.")
			
		data = self.to_record()
		for key, value in kwargs.items():
			if key in data:
				data[key] = value
				
		result = self.supabase_client.table("events").update(data).match({"id": self.id}).execute()
		return result

    # id, calendar_ids, title, description, start_timestamp, end_timestamp, age_timestamp
