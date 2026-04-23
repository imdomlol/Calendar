from utils.supabase_client import get_supabase_client
from models.guest import Guest
from models.calendar import Calendar
from models.event import Event
from models.external import External
from typing import Any


class User(Guest):
    # User extends Guest, so it inherits viewCalendar, viewEvent, editCalendar, editEvent
    # on top of that, User has a userId and can do full CRUD on everything

    def __init__(self, user_id: str, display_name: str, email: str) -> None:
        self.user_id = user_id
        self.display_name = display_name
        self.email = email
        # friends is just a list of user ids that this user has added
        self.friends: list[str] = []

    # -------------------------
    # Calendar stuff
    # -------------------------

    def listCalendars(self) -> list:
        # get all calendars this user owns or is a member of
        db = get_supabase_client()
        owned = db.table("calendars").select("*").eq("owner_id", self.user_id).execute()
        member = db.table("calendars").select("*").contains("member_ids", [self.user_id]).execute()
        # combine and deduplicate by id
        seen = {}
        for c in (owned.data or []) + (member.data or []):
            seen[c["id"]] = c
        return list(seen.values())

    def listEvents(self) -> list:
        # get all events that belong to any of this user's calendars
        db = get_supabase_client()
        calIds = [c["id"] for c in self.listCalendars()]
        if len(calIds) == 0:
            return []
        result = db.table("events").select("*").overlaps("calendar_ids", calIds).execute()
        return result.data or []

    def listExternals(self) -> list:
        # get all external calendar connections for this user
        db = get_supabase_client()
        result = db.table("externals").select("*").eq("user_id", self.user_id).execute()
        return result.data or []

    def createCalendar(self, name: str) -> Any:
        # make a new calendar owned by this user
        cal = Calendar(name=name, owner_id=self.user_id)
        return cal.save()

    def removeCalendar(self, calendar_id: str) -> Any:
        # delete a calendar by id
        cal = Calendar(name="", owner_id=self.user_id)
        cal.id = calendar_id
        return cal.remove_calendar()

    def addMember(self, calendar_id: str, member_id: str) -> Any:
        # load the calendar from the db first so we have the current member list
        db = get_supabase_client()
        result = db.table("calendars").select("*").eq("id", calendar_id).execute()
        if not result.data:
            raise ValueError("Calendar not found")
        calData = result.data[0]
        cal = Calendar(name=calData["name"], owner_id=calData["owner_id"])
        cal.id = calendar_id
        cal.member_ids = calData["member_ids"]
        return cal.add_member(member_id)

    def removeMember(self, calendar_id: str, member_id: str) -> Any:
        # load the calendar then remove the member from its list
        db = get_supabase_client()
        result = db.table("calendars").select("*").eq("id", calendar_id).execute()
        if not result.data:
            raise ValueError("Calendar not found")
        calData = result.data[0]
        cal = Calendar(name=calData["name"], owner_id=calData["owner_id"])
        cal.id = calendar_id
        cal.member_ids = calData["member_ids"]
        return cal.remove_member(member_id)

    # -------------------------
    # Event stuff
    # -------------------------

    def createEvent(self, title: str, calendar_ids: list[str], description: str | None = None, start_timestamp: str | None = None, end_timestamp: str | None = None) -> Any:
        # create a new event and save it to the db
        db = get_supabase_client()
        event = Event(
            title=title,
            supabase_client=db,
            calendar_ids=calendar_ids,
            owner_id=self.user_id,
            description=description,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
        return event.save()

    def editEvent(self, event_id: str, title: str | None = None, description: str | None = None, start_timestamp: str | None = None, end_timestamp: str | None = None, calendar_ids: list[str] | None = None) -> Any:
        # load the event from the db then call edit on it
        # this overrides Guest.editEvent because User can also change calendar_ids
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", event_id).execute()
        if not result.data:
            raise ValueError("Event not found")
        eventData = result.data[0]
        event = Event(
            title=eventData["title"],
            supabase_client=db,
            calendar_ids=eventData["calendar_ids"],
            owner_id=eventData["owner_id"],
        )
        event.id = event_id
        return event.edit(
            title=title,
            description=description,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            calendar_ids=calendar_ids,
        )

    def removeEvent(self, event_id: str) -> Any:
        # load the event then delete it
        db = get_supabase_client()
        result = db.table("events").select("*").eq("id", event_id).execute()
        if not result.data:
            raise ValueError("Event not found")
        eventData = result.data[0]
        event = Event(
            title=eventData["title"],
            supabase_client=db,
            calendar_ids=eventData["calendar_ids"],
        )
        event.id = event_id
        return event.remove()

    # -------------------------
    # External calendar stuff
    # -------------------------

    def linkExternal(self, url: str, provider: str, access_token: str | None = None, refresh_token: str | None = None) -> Any:
        # link an external calendar (like google) to this user
        db = get_supabase_client()
        ext = External(
            id=None,
            owner_id=self.user_id,
            url=url,
            provider=provider,
            supabase_client=db,
            user_id=self.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        return ext.save()

    def unlinkExternal(self, external_id: str) -> Any:
        # remove a single external calendar link
        db = get_supabase_client()
        return db.table("externals").delete().eq("id", external_id).execute()

    def pullDataCalendars(self, external_id: str) -> Any:
        # get the external record so we know what to pull from
        db = get_supabase_client()
        result = db.table("externals").select("*").eq("id", external_id).execute()
        return result.data

    def pushDataCalendars(self, external_id: str) -> Any:
        # get the external record so we know where to push to
        db = get_supabase_client()
        result = db.table("externals").select("*").eq("id", external_id).execute()
        return result.data

    # -------------------------
    # Friend stuff
    # -------------------------

    def viewFriendsList(self) -> list[str]:
        # just return the current friends list
        return self.friends

    def addFriend(self, user_id: str) -> None:
        # cant add yourself
        if user_id == self.user_id:
            raise ValueError("User cannot add themselves as a friend")
        # check if already in the list
        if user_id in self.friends:
            raise ValueError(f"User {user_id} is already a friend.")
        self.friends.append(user_id)

    def removeFriend(self, user_id: str) -> None:
        if user_id not in self.friends:
            raise ValueError(f"User {user_id} is not in the friends list")
        self.friends.remove(user_id)

    # -------------------------
    # Account stuff
    # -------------------------

    def removeAccount(self) -> Any:
        # delete this user's record from the users table
        db = get_supabase_client()
        return db.table("users").delete().eq("id", self.user_id).execute()

    def __repr__(self) -> str:
        return f"<User: {self.display_name}>"
