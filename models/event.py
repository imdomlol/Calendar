from utils.supabase_client import get_supabase_client
from typing import Any


# ========================= Event Model =========================


class Event:
    # make a new local event object before saving it
    def __init__(
        self,
        title: str,
        calendarIds: list[str],
        ownerId: str | None = None,
        description: str | None = None,
        startTimestamp: str | None = None,
        endTimestamp: str | None = None,
    ) -> None:
        self.id: str | None = None
        self.ownerId = ownerId
        self.title = title
        self.calendarIds = calendarIds
        self.description = description
        self.startTimestamp = startTimestamp
        self.endTimestamp = endTimestamp
        self.ageTimestamp: str | None = None

    # turn this event into a Supabase row
    def to_record(self) -> dict[str, Any]:
        rec = {
            "owner_id": self.ownerId,
            "calendar_ids": self.calendarIds,
            "title": self.title,
            "description": self.description,
            "start_timestamp": self.startTimestamp,
            "end_timestamp": self.endTimestamp,
        }
        if self.id is not None:
            rec["id"] = self.id
        if self.ageTimestamp is not None:
            rec["age_timestamp"] = self.ageTimestamp
        return rec

    # save this event and link it to calendars
    def save(self) -> Any:
        db = get_supabase_client()

        # insert the event row first
        query = db.table("events")
        query = query.insert(self.to_record())
        result = query.execute()
        rows = result.data or []

        if rows:
            newId = rows[0].get("id")
            self.id = newId

            try:
                # keep the cached calendar event lists updated
                Event.add_to_cal(newId, self.calendarIds or [])
            except Exception:
                # event lookup uses events calendar_ids
                # calendars events is only used for display
                # a cache issue should not break the insert
                pass

        return result

    # remove this event from the database
    def remove(self) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before it can be removed")

        db = get_supabase_client()

        # delete the event row
        query = db.table("events")
        query = query.delete()
        query = query.match({"id": self.id})
        result = query.execute()

        # also clean up each calendar cache
        Event.rm_from_cal(self.id, self.calendarIds or [])
        return result

    @staticmethod
    # add this event id to every linked calendar
    def add_to_cal(eventId, calIds) -> None:
        if not eventId or not calIds:
            return

        db = get_supabase_client()
        for calId in calIds:
            # load the current cached event ids for this calendar
            query = db.table("calendars")
            query = query.select("events")
            query = query.eq("id", calId)
            query = query.limit(1)
            row = query.execute()

            if not row.data:
                continue

            current = row.data[0].get("events") or []
            if eventId not in current:
                current.append(eventId)

                # write back the cache with the new event id
                updateQuery = db.table("calendars")
                updateQuery = updateQuery.update({"events": current})
                updateQuery = updateQuery.eq("id", calId)
                updateQuery.execute()

    @staticmethod
    # remove this event id from every linked calendar
    def rm_from_cal(eventId, calIds) -> None:
        if not eventId or not calIds:
            return

        db = get_supabase_client()
        for calId in calIds:
            # read the cached ids before changing them
            query = db.table("calendars")
            query = query.select("events")
            query = query.eq("id", calId)
            query = query.limit(1)
            row = query.execute()

            if not row.data:
                continue

            current = row.data[0].get("events") or []
            if eventId in current:
                current.remove(eventId)

                # save the smaller cached list
                updateQuery = db.table("calendars")
                updateQuery = updateQuery.update({"events": current})
                updateQuery = updateQuery.eq("id", calId)
                updateQuery.execute()

    @staticmethod
    # find one event row by id
    def find(eventId: str) -> dict | None:
        db = get_supabase_client()

        # ask Supabase for only this event
        query = db.table("events")
        query = query.select("*")
        query = query.eq("id", eventId)
        query = query.limit(1)
        result = query.execute()
        rows = result.data or []

        if rows:
            return rows[0]
        return None

    # update fields on a saved event
    def edit(self, title=None, description=None, startTimestamp=None, endTimestamp=None, calendarIds=None) -> Any:
        if self.id is None:
            raise ValueError("Event must be saved before it can be edited")

        # build only the fields the caller wants to change
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if startTimestamp is not None:
            updates["start_timestamp"] = startTimestamp
        if endTimestamp is not None:
            updates["end_timestamp"] = endTimestamp
        if calendarIds is not None:
            updates["calendar_ids"] = calendarIds

        db = get_supabase_client()

        # send the update to Supabase
        query = db.table("events")
        query = query.update(updates)
        query = query.match({"id": self.id})
        result = query.execute()

        if calendarIds is not None:
            oldIds = self.calendarIds or []
            newIds = calendarIds or []

            # find calendars that were added to the event
            toAdd = []
            for calId in newIds:
                if calId not in oldIds:
                    toAdd.append(calId)

            # find calendars that no longer need this event
            toRemove = []
            for calId in oldIds:
                if calId not in newIds:
                    toRemove.append(calId)

            Event.add_to_cal(self.id, toAdd)
            Event.rm_from_cal(self.id, toRemove)
            self.calendarIds = newIds

        return result
