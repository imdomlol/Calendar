from models.user import User
from utils.supabase_client import get_supabase_client
from utils.logger import logEvent
from typing import Any


class Admin(User):
    # Admin inherits from User and gets all the regular user stuff
    # plus these extra admin-only actions

    def suspendUserAccount(self, userId: str) -> Any:
        # suspend a user by removing all their externals and calendars
        # this is the simplest way to lock someone out without touching auth
        db = get_supabase_client()
        # remove all their external calendar links
        db.table("externals").delete().eq("user_id", userId).execute()
        # remove all calendars they own
        result = db.table("calendars").delete().eq("owner_id", userId).execute()
        logEvent("INFO", "admin", f"admin suspended user {userId}", userId=userId)
        return result

    def viewSystemLogs(self) -> Any:
        # pull all logs from the logs table
        db = get_supabase_client()
        result = db.table("logs").select("*").execute()
        return result.data

    def sendSystemWideNotifications(self, message: str) -> None:
        # log the notification so it shows up in the system logs
        # in the future this could send emails or push notifications
        logEvent("INFO", "notification", message)

    def unlinkAllExternalCalendars(self, userId: str) -> Any:
        # remove every external calendar linked to a specific user
        db = get_supabase_client()
        result = db.table("externals").delete().eq("user_id", userId).execute()
        return result
