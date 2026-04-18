# Calendar functions
'''
class Calendar:
    __init__:
        x
    to_record:
        Dictionary: Save a data records of the user, and related credentials.
    save:
        Save the calendar to the database.
    remove_calendar:
        Opposite of the save function. Remove the calendar (+ Events, member_ids, dates) from the database.
    add_event:
        x
    add_member:
        Take a member's user_id, and add it to the member_ids list - These users have access to the calendar.
    remove_member:
        Opposite of the add function. Remove the member from the list, thus removing access to calendar.
'''

from typing import Any
from utils.supabase_client import get_supabase_client

class InvalidUserID(Exception):                         # Custom Error raised for add_member()
    pass                                                # Invalid ID: Length, Characters, DNE, etc.
    '''
    Other custom errors to consider
        UserNotFound
        DuplicateID
        OwnerID
    '''

class Calendar:
    def __init__(self, name: str, owner_id: str) -> None:
        self.id = None                                  # Will be set when the calendar is saved to the database. The calendar to save, edit, remove
        self.name = name                                # The name of the calendar, e.g. "Work Calendar", "Personal Calendar", etc
        self.owner_id = owner_id                        # The ID of the user who owns the calendar
        self.member_ids: list[str] = [owner_id]         # A list of IDs of users who have access to the calendar
        self.events: list[str] = []                     # A list of IDs of events associated with the calendar
        self.age_timestamp = None                       # Will be set when the calendar is saved to the database

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
        return (
            supabase                                    # Link to the supabase client.
            .table("calendars")                         # From the database, select 'calendars' to target for insertion.
            .insert(self.to_record())                   # Insert the calendar data, returns a dictionary of calendar info.
            .execute()                                  # Perform the actions, otherwise nothing occurs.
        )

    def remove_calendar(self):
        supabase = get_supabase_client()
        return (
            supabase
            .table("calendars")
            .delete()                                   # Delete the target, apply filtering to avoid deleting the wrong objects.
            .eq("id", self.id)                          # "Equals", filter out so the correct calendar id is matched.
            .execute()
        )

    def add_event(self, event_id: str) -> None:
        self.events.append(event_id)                    # Add an event ID to the calendar's list of events
    
    def add_member(self, new_member: str):              # Adds a new member to a calendar class object.
        if new_member == self.owner_id:                 # Ensure that the ID != owner_id.
            raise InvalidUserID(": Cannot add owner_id to member list.") # Otherwise raise error
        if self.id == None:
            raise ValueError(": self.id does not exist.")
        if new_member in self.member_ids:               # Ensure that the ID isn't already in the list.
            print("Heads up!: The member you are trying to add is already in the members list.") # No error, just message.
            return None                                 # Member is already in the list; no changes made to database, break function - no need for Exception.
        
        supabase = get_supabase_client()                # Connect to supabase client.
        try: # Error handling; Ensure that the member_id exists in the db before proceeding to the append function.
            response = (                                # Record the return from supabase to a variable, to be used in an if function.
                supabase
                .table("users")
                .select("id")                           # Further select the "id" column from the "users" table.
                .eq("id", new_member)                   # Check if the "id" column has a value that matches the new_member variable.
                .execute()
            )
        except Exception as err:
            raise RuntimeError(f"{err}: Supabase query failed.") # RuntimeError = Common base class for all exceptions

        if not response.data: # response.data = [] is returned instead: member_id DNE. Also includes response.error
            raise ValueError(": member_id does not exist.")
        
        self.member_ids.append(new_member)              # No Errors = Append the new member to the member_ids list.
        return (                                        # Update the Supabase client.
            supabase                                    
            .table("calendars")
            .update({"member_ids":self.member_ids})     # Update the member_ids column with the new member_ids list.
            .eq("id", self.id)                          # Filter to ensure the correct calendar is updated, via matching the calendar id.
            .execute()
        )

    def remove_member(self, del_member: str):           # Opposite function of the add_member() from above.
        supabase = get_supabase_client()                # Connect to supabase.
        if del_member not in self.member_ids:           # Raise error if the member to delete isn't in the member_ids list.
            raise KeyError("Member not found.")
        else:                                           # Otherwise, proceed to viciously murder the member_id from the list, no funeral.
            self.member_ids.remove(del_member)          # Remove the member from the member_ids list.
            return (
                supabase
                .table("calendars")
                .update({"member_ids": self.member_ids})
                .eq("id", self.id)
                .execute()
            )