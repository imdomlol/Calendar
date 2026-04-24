from utils.supabase_client import get_supabase_client
from models.guest import Guest
from typing import Any


class User(Guest):
    # User extends Guest, so it inherits viewCalendar, viewEvent, editCalendar, editEvent
    # on top of that, User has a userId and can do full CRUD on everything

    def __init__(self, userId: str, displayName: str, email: str) -> None:
        self.userId = userId
        self.displayName = displayName
        self.email = email

    # -------------------------
    # Calendar stuff
    # -------------------------

    def listCalendars(self) -> list:
        # get all calendars this user owns or is a member of
        db = get_supabase_client()
        owned = db.table("calendars").select("*").eq("owner_id", self.userId).execute()
        member = db.table("calendars").select("*").contains("member_ids", [self.userId]).execute()
        # combine and deduplicate by id
        allCals = []
        seenIds = []
        for c in (owned.data or []):
            allCals.append(c)
            seenIds.append(c["id"])
        for c in (member.data or []):
            if c["id"] not in seenIds:
                allCals.append(c)
        return allCals

    # -------------------------
    # Event stuff
    # -------------------------

    def listEvents(self) -> list:
        # get all events that belong to any of this user's calendars
        db = get_supabase_client()
        calIds = [c["id"] for c in self.listCalendars()]
        if not calIds:
            return []
        result = db.table("events").select("*").overlaps("calendar_ids", calIds).execute()
        return result.data or []

    def listEventsForCalendar(self, calendarId: str) -> list:
        from models.calendar import Calendar
        return Calendar.listEvents(calendarId)

    # -------------------------
    # External calendar stuff
    # -------------------------

    def listExternals(self) -> list:
        # get all external calendar connections for this user
        db = get_supabase_client()
        result = db.table("externals").select("*").eq("user_id", self.userId).execute()
        return result.data or []

    # -------------------------
    # Friend stuff
    # -------------------------

    def listFriends(self) -> list:
        # get the friends list (IDs) from the database
        db = get_supabase_client()
        result = db.table("users").select("friends").eq("id", self.userId).execute()
        if not result.data:
            return []
        return result.data[0].get("friends") or []

    def listFriendsData(self) -> list:
        # resolve friend IDs to full user records
        friendIds = self.listFriends()
        if not friendIds:
            return []
        db = get_supabase_client()
        result = db.table("users").select("id, email, display_name").in_("id", friendIds).execute()
        return result.data or []

    def addFriend(self, friendId: str = None, email: str = None) -> list:
        # if no friendId given but email is, look up the user by email
        db = get_supabase_client()
        if friendId is None and email is not None:
            result = db.table("users").select("id").eq("email", email).execute()
            if not result.data:
                raise ValueError("No user found with that email")
            friendId = result.data[0]["id"]

        if friendId is None:
            raise ValueError("friend_id or email is required")

        # cant add yourself
        if friendId == self.userId:
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
        # delete this user's record from the users table
        db = get_supabase_client()
        return db.table("users").delete().eq("id", self.userId).execute()

    def __repr__(self) -> str:
        return f"<User: {self.displayName}>"
