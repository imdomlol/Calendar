from utils.supabase_client import get_supabase_client
from typing import Any


class User:
    def __init__(self, display_name: str, email: str) -> None:
        # set up the user object with a name and email
        # id is None until this gets saved to the database
        self.id = None
        # display_name is what shows up in the ui for this user
        self.display_name = display_name
        # these start as None and get loaded from the database later
        self.calendars = None
        self.events = None
        self.externals = None
        self.email = email
        # friends is just a list of user ids
        self.friends: list[str] = []


    def to_record(self) -> dict[str, Any]:
        rec = {
            "id": self.id,
            "calendars": self.calendars,
            "events": self.events,
            "externals": self.externals,
        }
        return rec

    def save(self) -> Any:
        db = get_supabase_client()
        return db.table("user").insert(self.to_record()).execute()


    def add_friend(self, user_id: str) -> None:
        # cant add yourself as a friend
        if user_id == self.id:
            raise ValueError("User cannot add themselves as a friend")
        # check if theyre already in the list
        alreadyFriend = user_id in self.friends
        if alreadyFriend == True:
            raise ValueError(f"User {user_id} is already a friend.")
        self.friends.append(user_id)

    def remove_friend(self, user_id: str) -> None:
        notPresent = user_id not in self.friends
        if notPresent:
            raise ValueError(f"User {user_id} is not in the friends list")
        self.friends.remove(user_id)
