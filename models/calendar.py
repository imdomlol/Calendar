from utils.supabase_client import get_supabase_client
from typing import Any


# ========================= Errors =========================


class InvalidUserId(Exception):
    # raised when a bad user id is added
    pass


# ========================= Calendar Model =========================


class Calendar:
    # make a local calendar object before saving it
    def __init__(self, name: str, ownerId: str) -> None:
        self.id = None
        self.name = name
        self.ownerId = ownerId
        self.memberIds: list[str] = [ownerId]
        self.events: list[str] = []
        self.ageTimestamp = None

    # turn the object into a Supabase row
    def to_record(self) -> dict[str, Any]:
        # keep these names matched with the DB columns
        rec = {
            "name": self.name,
            "owner_id": self.ownerId,
            "member_ids": self.memberIds,
            "events": self.events,
        }

        # only send id when one already exists
        if self.id is not None:
            rec["id"] = self.id

        # let the DB set the age timestamp when missing
        if self.ageTimestamp is not None:
            rec["age_timestamp"] = self.ageTimestamp

        return rec

    # save this calendar in the DB
    def save(self) -> Any:
        db = get_supabase_client()
        record = self.to_record()
        query = db.table("calendars")
        result = query.insert(record).execute()
        return result

    # remove this calendar and clean up linked events
    def remove(self) -> Any:
        db = get_supabase_client()

        # load events that still point at this calendar
        eventsQuery = db.table("events")
        eventsQuery = eventsQuery.select("id, calendar_ids")
        eventsQuery = eventsQuery.contains("calendar_ids", [self.id])
        eventsResult = eventsQuery.execute()

        eventRows = eventsResult.data or []
        for row in eventRows:
            currentIds = row.get("calendar_ids") or []
            remaining = []

            # keep every other calendar id on the event
            for calId in currentIds:
                if calId != self.id:
                    remaining.append(calId)

            if remaining:
                updateQuery = db.table("events")
                updateQuery = updateQuery.update({"calendar_ids": remaining})
                updateQuery.eq("id", row["id"]).execute()
            else:
                deleteEventQuery = db.table("events")
                deleteEventQuery.delete().eq("id", row["id"]).execute()

        deleteCalendarQuery = db.table("calendars")
        result = deleteCalendarQuery.delete().eq("id", self.id).execute()
        return result

    # add a user to the member list
    def add_member(self, newMember: str) -> Any:
        if newMember == self.ownerId:
            raise InvalidUserId("Cannot add the owner to the member list")

        if self.id is None:
            raise ValueError("Calendar must be saved before adding members")

        if newMember in self.memberIds:
            return None

        db = get_supabase_client()

        try:
            # make sure the user exists first
            userQuery = db.table("users")
            userQuery = userQuery.select("id")
            result = userQuery.eq("id", newMember).execute()
        except Exception as err:
            raise RuntimeError(f"Supabase query failed: {err}")

        if not result.data:
            raise ValueError("Member id does not exist")

        self.memberIds.append(newMember)

        # write the new member list back
        updateQuery = db.table("calendars")
        updateQuery = updateQuery.update({"member_ids": self.memberIds})
        result = updateQuery.eq("id", self.id).execute()
        return result

    # remove a user from the member list
    def remove_member(self, delMember: str) -> Any:
        if delMember == self.ownerId:
            raise InvalidUserId("Cannot remove the owner from the member list")

        if self.id is None:
            raise ValueError("Calendar must be saved before removing members")

        if delMember not in self.memberIds:
            raise KeyError("Member not found")

        db = get_supabase_client()
        self.memberIds.remove(delMember)

        updateQuery = db.table("calendars")
        updateQuery = updateQuery.update({"member_ids": self.memberIds})
        result = updateQuery.eq("id", self.id).execute()
        return result

    # find a calendar that matches a public guest token
    @staticmethod
    def find_by_guest_token(token: str) -> dict | None:
        db = get_supabase_client()

        # only active guest links should be returned
        query = db.table("calendars")
        query = query.select("id, name, owner_id, guest_link_token, guest_link_role, guest_link_active")
        query = query.eq("guest_link_token", token)
        query = query.eq("guest_link_active", "true")
        result = query.limit(1).execute()

        rows = result.data or []
        if rows:
            return rows[0]
        return None

    # list events that belong to a calendar
    @staticmethod
    def list_events(calendarId: str) -> list:
        db = get_supabase_client()

        # cast the id so the DB array comparison is consistent
        calendarIds = [str(calendarId)]

        query = db.table("events")
        query = query.select("*")
        query = query.overlaps("calendar_ids", calendarIds)
        query = query.order("start_timestamp", desc=False)
        result = query.execute()

        return result.data or []
