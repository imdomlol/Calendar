# Calendar functions, contains the following:
'''
class Calendar:
    __init__:
        x
    add_event:
        x
    to_record:
        x
    save:
        x
    remove_calendar:
        Remove the called-upon calendar (+ Events, member_ids, dates)
'''
from typing import Any
from utils.supabase_client import get_supabase_client

class Calendar: # 
    def __init__( # 
        self,
        name: str,
        owner_id: str,
    ) -> None:
        
        self.id = None # Will be set when the calendar is saved to the database. The calendar to save, edit, remove.
        self.name = name # 
        self.owner_id = owner_id # 
        self.member_ids: list[str] = [owner_id] # 
        self.events: list[str] = [] # 
        self.age_timestamp = None # Will be set when the calendar is saved to the database

    def add_event(self, event_id: str) -> None: # 
        '''
        self = 
        events = 
        append(event_id) = 
        '''
        self.events.append(event_id) # 

    def to_record(self) -> dict[str, Any]: # Dictionary: Save a data records of the user, and related credentials.
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "member_ids": self.member_ids,
            "events": self.events,
            "age_timestamp": self.age_timestamp,
        }
    
    def save(self) -> Any: # Save the calendar to the database. 
        supabase = get_supabase_client() # Connect to supabase client.
        '''
        supabase = Link to the supabase client.
        .table("calendars") = From the database, select 'calendars' to target for insertion.
        .insert(self.to_record()) = 
            to_record() = Returns a dictionary of calendar info, refer to def to_record() above.
        .execute() = Perform the actions above, otherwise the line would just be saved.
        '''
        return supabase.table("calendars").insert(self.to_record()).execute() # 

    def remove_calendar(self): # Removes the calendar from the database. Opposite of the save function above.
        supabase = get_supabase_client() # Connect to supabase; Use in removing the calendar from the cilent.
        '''
        supabase = Link to the supabase client.
        .table("calendars") = From the database, select 'calendars' as target for removal.
        .delete() = Delete the target, apply filtering to avoid deleting the wrong objects.
        .eq("id", self.id) = "Equals", filter out so the correct calendar id is matched.
        .execute() = Perform the actions above, otherwise the line would just be saved.
        '''
        return supabase.table("calendars").delete().eq("id", self.id).execute() # 










'''
STORAGE
    #import datetime # 
    #import time # 

    #self.events.calendar_id

    # Find members, events, age, if calendar contains such.
    #self.member_ids.delete() if "id" == self.id

    calendar_id = self.id # Target calendar.
'''