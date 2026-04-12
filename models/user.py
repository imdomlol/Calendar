# User functions, contains the following:
# 03 / 27 / 2026
'''
class User:
    __init__
        Initalization of the User class; neccessary for the inital setup of any class. For the User class, it'll set up:
            self.id = User's id, 
            self.display_name = User's display name, for display on their personal account, calendar, friends list, events.
            self.calendars = User's calendars - list of calendars the user owns, should they have 1, or multiple.
            self.events = User's uniqe events - Not per calendar, but global per calendar.
            self.externals = User's imported calendar data from external APIs.
            self.email = User email, for login, providing invite links, notifications, promotional codes.
    to_record()
        Imported from Calendar class, modified for the User class. 
            "id" = 
            "calendars" = 
            "events" = 
            "externals" = 
    save()
        Create user table for Supabase, calls upon to_record().
            DECRIPTION
    function3
        DECRIPTION
    function4
        DECRIPTION
    function5
        DECRIPTION
'''

# Imports
from typing import Any # 
from utils.supabase_client import get_supabase_client # 

from calendar import Calendar
from event import Event
from external import External
'''
Import the classes from the modules, for the User to interact with.
    xxx
'''


class User:
    def __init__(self, display_name: str, email: str) -> None:
        self.id = None
        self.display_name = display_name
        self.calendars = None #Calendar(self.display_name, self.id) # name, owner_id
        self.events = None #Event() # title, supabase_client, calendar_ids, owner_id, description, start_timestamp, end_timestamp
        self.externals = None #External() # 
        self.email = email
    '''
    Other self.variables: [ REMOVED ]
        self.owner_id = owner_id # Calendar's id.
        self.name = name # Unique name, immutable. 
        self.role = role # Determine whether the user being called is an "owner" OR "user", "friend", "viewer", "editor", etc. THIS CASE: "user"
        self.password_hash = user_password #hash_password(user_password) # User password for login, security. [ hash_password() would be a function...? ]

        name: str, user_password: str, role: str
    '''

    def to_record(self) -> dict[str, Any]: # Returns dictionary of variables below.
        return {
            "id": self.id,
            "calendars": self.calendars,
            "events": self.events,
            "externals": self.externals
        }
    '''
    REMOVED:
        "owner_id": self.owner_id,
        "name": self.name,
        "member_ids": self.member_ids,
        "age_timestamp": self.age_timestamp,
    '''

    def save(self) -> Any:
        supabase = get_supabase_client() # Connect to supabase client.
        return supabase.table("user").insert(self.to_record()).execute() # 
    '''
    supabase = Link to the supabase client.
    .table("user") = From the database, select 'user' to target for insertion.
    .insert(self.to_record()) = 
        to_record() = Returns a dictionary of user info, refer to def to_record() above.
    .execute() = Perform the actions above, otherwise the line would just be saved.
    '''

    def function3(): # 
        return None
    '''
    COMMENTS ABOUT THE FUNCTION.
    '''
    
    def function4(): # 
        return None
    '''
    COMMENTS ABOUT THE FUNCTION.
    '''
    
    def function5(): # 
        return None
    '''
    COMMENTS ABOUT THE FUNCTION.
    '''





# Storage ===============================================================================================================================
'''
Ideas to implement
    calendar manager
        call calendar class
    event manager
        call event class
    external control
        call external class


User will need to be able to do the operations below, so calling the apporiate classes is neccessary: ( Imported from FigJam UML )
    Manage externals
        x
    Manage accounts (self)
        Create account (EX: One for school, work, personal)
        Delete account
        Change preferances 

    Manage friends / outside access
        Add, remove, set permissions, 



AI GENERATED IDEAS:
    update_profile(self, **kwargs): A flexible function to update metadata like display names or profile pictures.

    create_event(self, title, start_time, end_time, **kwargs): Factory method to instantiate event objects tied to this user.

    get_upcoming_events(self, limit=5): Returns a filtered list of events starting from the current datetime.now().

    is_available(self, start_time, end_time): A critical helper function that checks the user's existing schedule for overlaps before booking a new slot.

    share_calendar_with(self, other_user, permission_level): Manages permissions (e.g., "read-only" vs. "editor").

    respond_to_invite(self, event_id, status): Handles "Accept," "Decline," or "Maybe" statuses.

    get_friend_busy_times(self, friend_id, date): A privacy-focused way to see when a contact is occupied without seeing their specific event details.

    get_timezone_offset(): Essential if your project will be used by people in different regions.

    __repr__ or __str__: Crucial for debugging in VS Code. It allows you to see <User: imdomlol> in the console instead of a generic memory address.
'''