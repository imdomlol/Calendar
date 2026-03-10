from typing import Any

class Events:
    def __init__(self, supabase_client):
        self.supabase_client = supabase_client

    def to_record(self, calendar_id: str, title: str, description: str, start_time: str, end_time: str) -> dict:
        return {
            "calendar_id": calendar_id,
            "title": title,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
        }
    
    def save(self, calendar_id: str, title: str, description: str, start_time: str, end_time: str) -> Any:
        record = self.to_record(calendar_id, title, description, start_time, end_time)
        return self.supabase_client.table("events").insert(record).execute()
    
    #id, calendar_id, title, description, start_at, end_at, created_at
    #id, calendar_ids, title, description, start_timestamp, end_timestamp, age_timestamp