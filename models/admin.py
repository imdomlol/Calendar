from models.user import User
from models.external import External
from utils.supabase_client import get_supabase_client
from utils.logger import get_logger_client, logEvent
from typing import Any


def _admin_db():
    # admins need the service role key so RLS does not block admin actions.
    db = get_logger_client()
    if db is None:
        db = get_supabase_client()
    return db


class Admin(User):
    # Admin inherits from User and gets all the regular user stuff
    # plus these extra admin-only actions

    @staticmethod
    def suspendUserAccount(userId: str) -> Any:
        db = _admin_db()
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
        db = _admin_db()
        result = db.table("logs").select("*").execute()
        return result.data

    @staticmethod
    def sendSystemWideNotifications(message: str) -> None:
        db = _admin_db()
        # turn off old active rows so only one banner can show at a time.
        db.table("notifications").update({"active": False}).eq("active", True).execute()
        new_row = {"message": message, "active": True}
        db.table("notifications").insert(new_row).execute()
        logEvent("INFO", "notification", message)

    @staticmethod
    def clearActiveNotifications() -> None:
        db = _admin_db()
        db.table("notifications").update({"active": False}).eq("active", True).execute()
        logEvent("INFO", "notification", "admin cleared active notifications")

    @staticmethod
    def getActiveNotificationMessage():
        db = _admin_db()
        result = (
            db.table("notifications")
            .select("message")
            .eq("active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0].get("message")
        return None

    @staticmethod
    def findUserByQuery(q):
        if not q:
            return None

        db = _admin_db()
        result = db.table("users").select("id, email, display_name").eq("email", q).limit(1).execute()
        if result.data:
            return result.data[0]

        result = db.table("users").select("id, email, display_name").eq("display_name", q).limit(1).execute()
        if result.data:
            return result.data[0]

        # ids are last so a display name that looks id-like still wins.
        result = db.table("users").select("id, email, display_name").eq("id", q).limit(1).execute()
        if result.data:
            return result.data[0]
        return None

    @staticmethod
    def listAllUsers():
        db = _admin_db()
        result = db.table("users").select("id, email, display_name, is_admin").execute()
        if result.data:
            return result.data
        return []

    @staticmethod
    def toggleUserAdmin(userId):
        db = _admin_db()
        current = db.table("users").select("is_admin").eq("id", userId).limit(1).execute()
        if not current.data:
            return None

        old_val = current.data[0].get("is_admin", False)
        if old_val:
            new_val = False
        else:
            new_val = True

        db.table("users").update({"is_admin": new_val}).eq("id", userId).execute()
        logEvent("INFO", "admin", "admin toggled is_admin on user " + str(userId) + " to " + str(new_val), userId=userId)
        return new_val

    @staticmethod
    def listExternalsForUser(userId):
        db = _admin_db()
        result = db.table("externals").select("id, provider, url").eq("user_id", userId).execute()
        if result.data:
            return result.data
        return []

    @staticmethod
    def unlinkAllExternalCalendars(userId: str) -> Any:
        db = _admin_db()
        result = db.table("externals").delete().eq("user_id", userId).execute()
        logEvent("INFO", "admin", "admin unlinked all externals for user " + str(userId), userId=userId)
        return result

    @staticmethod
    def unlinkExternalById(externalId):
        db = _admin_db()
        # look up the owner so External.remove can keep provider cleanup behavior.
        lookup = db.table("externals").select("id, user_id").eq("id", externalId).limit(1).execute()
        if not lookup.data:
            return False

        owner_id = lookup.data[0].get("user_id")
        ext = External(id=externalId, supabaseClient=db, userId=owner_id)
        ext.remove(externalId)
        logEvent("INFO", "admin", "admin unlinked external " + str(externalId), userId=owner_id)
        return True
