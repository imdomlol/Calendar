# Calendar functions, contains the following:
'''
class Calendar:
    __init__:
        x
    add_event:
        x
    to_record:
        Dictionary: Save a data records of the user, and related credentials.
    save:
        Save the calendar to the database. 
    remove_calendar:
        Remove the calendar (+ Events, member_ids, dates) from the database. Opposite of the save function.

'''

from typing import Any
from utils.supabase_client import get_supabase_client

class Calendar:
    def __init__(self, name: str, owner_id: str) -> None:
        self.id = None # Will be set when the calendar is saved to the database. The calendar to save, edit, remove
        self.name = name # The name of the calendar, e.g. "Work Calendar", "Personal Calendar", etc
        self.owner_id = owner_id # The ID of the user who owns the calendar
        self.member_ids: list[str] = [owner_id] # A list of IDs of users who have access to the calendar
        self.events: list[str] = [] # A list of IDs of events associated with the calendar
        self.age_timestamp = None # Will be set when the calendar is saved to the database

    def add_event(self, event_id: str) -> None:
        self.events.append(event_id) # Add an event ID to the calendar's list of events

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
        supabase = get_supabase_client()
        '''
        supabase = Link to the supabase client.
        .table("calendars") = From the database, select 'calendars' to target for insertion.
        .insert(self.to_record()) = 
            to_record() = Returns a dictionary of calendar info, refer to def to_record() above.
        .execute() = Perform the actions above, otherwise the line would just be saved.
        '''
        return supabase.table("calendars").insert(self.to_record()).execute() # 

    def remove_calendar(self):
        supabase = get_supabase_client()
        '''
        supabase = Link to the supabase client.
        .table("calendars") = From the database, select 'calendars' as target for removal.
        .delete() = Delete the target, apply filtering to avoid deleting the wrong objects.
        .eq("id", self.id) = "Equals", filter out so the correct calendar id is matched.
        .execute() = Perform the actions above, otherwise the line would just be saved.
        '''
        return supabase.table("calendars").delete().eq("id", self.id).execute()