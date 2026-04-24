from models.user import User
from utils.supabase_client import get_supabase_client
from utils.logger import logEvent
from typing import Any


class Admin(User):
    # Admin inherits from User and gets all the regular user stuff
    # plus these extra admin-only actions

    @staticmethod
    def suspendUserAccount(userId: str) -> Any:
        db = get_supabase_client()
        # delete externals first so the user loses external access even if the calendar delete fails
        try:
            db.table("externals").delete().eq("user_id", userId).execute()
        except Exception as err:
            logEvent("ERROR", "admin", f"suspendUserAccount: failed to delete externals for {userId}: {err}", userId=userId)
            raise
        try:
            result = db.table("calendars").delete().eq("owner_id", userId).execute()
        except Exception as err:
            logEvent("ERROR", "admin", f"suspendUserAccount: externals removed but calendar delete failed for {userId}: {err}", userId=userId)
            raise
        logEvent("INFO", "admin", f"admin suspended user {userId}", userId=userId)
        return result

    @staticmethod
    def viewSystemLogs() -> Any:
        db = get_supabase_client()
        result = db.table("logs").select("*").execute()
        return result.data

    @staticmethod
    def sendSystemWideNotifications(message: str) -> None:
        logEvent("INFO", "notification", message)

    @staticmethod
    def unlinkAllExternalCalendars(userId: str) -> Any:
        db = get_supabase_client()
        result = db.table("externals").delete().eq("user_id", userId).execute()
        return result
