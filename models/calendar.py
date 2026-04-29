from utils.supabase_client import get_supabase_client
from typing import Any


class InvalidUserID(Exception):
    # raised when an invalid user id is passed to add_member
    pass


class Calendar:
    def __init__(self, name: str, ownerId: str) -> None:
        self.id = None              # set when saved to the database
        self.name = name
        self.ownerId = ownerId
        self.memberIds: list[str] = [ownerId]   # owner is always a member
        self.events: list[str] = []
        self.ageTimestamp = None    # set when saved to the database

    def to_record(self) -> dict[str, Any]:
        # build a dict with column names matching the calendars table in supabase
        # omit id and age_timestamp when None so the DB default kicks in
        rec = {
            "name": self.name,
            "owner_id": self.ownerId,
            "member_ids": self.memberIds,
            "events": self.events,
        }
        if self.id is not None:
            rec["id"] = self.id
        if self.ageTimestamp is not None:
            rec["age_timestamp"] = self.ageTimestamp
        return rec

    def save(self) -> Any:
        # insert this calendar into the database
        db = get_supabase_client()
        return db.table("calendars").insert(self.to_record()).execute()

    def remove(self) -> Any:
        # delete this calendar from the database; clean up orphaned events first
        db = get_supabase_client()
        events_result = db.table("events").select("id, calendar_ids").contains("calendar_ids", [self.id]).execute()
        for row in (events_result.data or []):
            remaining = [c for c in (row.get("calendar_ids") or []) if c != self.id]
            if remaining:
                db.table("events").update({"calendar_ids": remaining}).eq("id", row["id"]).execute()
            else:
                db.table("events").delete().eq("id", row["id"]).execute()
        return db.table("calendars").delete().eq("id", self.id).execute()

    def add_member(self, newMember: str) -> Any:
        # add a user to this calendar's member list
        if newMember == self.ownerId:
            raise InvalidUserID("Cannot add the owner to the member list")
        if self.id is None:
            raise ValueError("Calendar must be saved before adding members")
        if newMember in self.memberIds:
            # already in the list, nothing to do
            return None

        # check that the user actually exists in the database
        db = get_supabase_client()
        try:
            result = db.table("users").select("id").eq("id", newMember).execute()
        except Exception as err:
            raise RuntimeError(f"Supabase query failed: {err}")

        if not result.data:
            raise ValueError("Member id does not exist")

        # add them and save the updated list
        self.memberIds.append(newMember)
        return db.table("calendars").update({"member_ids": self.memberIds}).eq("id", self.id).execute()

    def remove_member(self, delMember: str) -> Any:
        # remove a user from this calendar's member list
        if delMember not in self.memberIds:
            raise KeyError("Member not found")
        db = get_supabase_client()
        self.memberIds.remove(delMember)
        return db.table("calendars").update({"member_ids": self.memberIds}).eq("id", self.id).execute()

    @staticmethod
    def findByGuestToken(token: str) -> dict | None:
        db = get_supabase_client()
        result = (
            db.table("calendars")
            .select("id, name, owner_id, guest_link_token, guest_link_role, guest_link_active")
            .eq("guest_link_token", token)
            .eq("guest_link_active", "true")
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    @staticmethod
    def listEvents(calendarId: str) -> list:
        db = get_supabase_client()
        result = (
            db.table("events")
            .select("*")
            .overlaps("calendar_ids", [str(calendarId)])
            .order("start_timestamp", desc=False)
            .execute()
        )
        return result.data or []
