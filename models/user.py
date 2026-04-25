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

        # load current friends list from the database
        currentFriends = self.listFriends()

        # check if already friends
        if friendId in currentFriends:
            raise ValueError(f"User {friendId} is already a friend")

        # add the new friend and save to the database
        currentFriends.append(friendId)
        db.table("users").update({"friends": currentFriends}).eq("id", self.userId).execute()
        return currentFriends

    def removeFriend(self, friendId: str) -> None:
        # load current friends list from the database
        db = get_supabase_client()
        currentFriends = self.listFriends()

        if friendId not in currentFriends:
            raise ValueError(f"User {friendId} is not in the friends list")

        # remove and save to the database
        currentFriends.remove(friendId)
        db.table("users").update({"friends": currentFriends}).eq("id", self.userId).execute()

    # -------------------------
    # Account stuff
    # -------------------------

    def removeAccount(self) -> Any:
        db = get_supabase_client()
        result = db.table("users").delete().eq("id", self.userId).execute()
        # also remove from Supabase auth so the user can't log back in
        db.auth.admin.delete_user(self.userId)
        return result

    def __repr__(self) -> str:
        return f"<User: {self.display_name}>"
