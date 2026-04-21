from typing import Any

from utils.supabase_client import get_supabase_client


class User:
    def __init__(self, display_name: str, email: str) -> None:
        self.id = None
        self.display_name = display_name
        self.calendars = None
        self.events = None
        self.externals = None
        self.email = email
        self.friends: list[str] = []

    def to_record(self) -> dict[str, Any]:
        """Returns a dict of user fields suitable for Supabase insertion."""
        return {
            "id": self.id,
            "calendars": self.calendars,
            "events": self.events,
            "externals": self.externals,
        }

    def save(self) -> Any:
        """Inserts this user into the Supabase 'user' table."""
        supabase = get_supabase_client()
        return supabase.table("user").insert(self.to_record()).execute()

    def add_friend(self, user_id: str) -> None:
        """Appends user_id to the friends list; raises if already present or self."""
        if user_id == self.id:
            raise ValueError("User cannot add themselves as a friend")
        if user_id in self.friends:
            raise ValueError(f"User {user_id} is already a friend.")
        self.friends.append(user_id)

    def remove_friend(self, user_id: str) -> None:
        """Removes user_id from the friends list; raises if not present."""
        if user_id not in self.friends:
            raise ValueError(f"User {user_id} is not in the friends list")
        self.friends.remove(user_id)

    def __repr__(self) -> str:
        return f"<User: {self.display_name}>"
