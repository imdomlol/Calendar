from models.user import User
from models.external import External
from utils.supabase_client import get_supabase_client
from utils.logger import get_logger_client, log_event
from typing import Any
from uuid import UUID


# ========================= Helpers =========================

# grab the admin DB client using the service role key so RLS doesnt block admin actions
def _admin_db():
    db = get_logger_client()
    if db is None:
        db = get_supabase_client()
    return db


# check if a string looks like a valid UUID
def _is_uuid(value: str) -> bool:
    try:
        UUID(str(value))
    except (TypeError, ValueError):
        return False
    return True


# ========================= Admin Class =========================

# Admin inherits from User and gets all the regular user stuff
# plus these extra admin only actions
class Admin(User):

    @staticmethod
    def suspend_user_account(userId: str) -> Any:
        # mark the account as suspended without deleting any of the users data
        db = _admin_db()
        try:
            result = db.table("users").update({"is_suspended": True}).eq("id", userId).execute()
        except Exception as err:
            log_event("ERROR", "admin", f"suspend_user_account: failed to suspend user {userId}: {err}", userId=userId)
            raise
        log_event("INFO", "admin", f"admin suspended user {userId}", userId=userId)
        return result

    @staticmethod
    def view_system_logs() -> Any:
        # pull all log rows from the logs table
        db = _admin_db()
        result = db.table("logs").select("*").execute()
        return result.data

    @staticmethod
    def send_system_wide_notifications(message: str) -> None:
        db = _admin_db()

        # turn off any currently active notification so only one banner shows at a time
        db.table("notifications").update({"active": False}).eq("active", True).execute()

        newRow = {"message": message, "active": True}
        db.table("notifications").insert(newRow).execute()
        log_event("INFO", "notification", message)

    @staticmethod
    def clear_active_notifications() -> None:
        # deactivate all notification rows
        db = _admin_db()
        db.table("notifications").update({"active": False}).eq("active", True).execute()
        log_event("INFO", "notification", "admin cleared active notifications")

    @staticmethod
    def get_active_notification_message():
        # grab the most recent active banner message
        db = _admin_db()
        query = db.table("notifications")
        query = query.select("message")
        query = query.eq("active", True)
        query = query.order("created_at", desc=True)
        query = query.limit(1)
        result = query.execute()

        if result.data:
            return result.data[0].get("message")
        return None

    @staticmethod
    def find_user_by_query(query):
        # clean up whitespace before searching
        query = str(query).strip()
        if not query:
            return None

        db = _admin_db()

        # try matching by email first
        result = db.table("users").select("id, email, display_name").eq("email", query).limit(1).execute()
        if result.data:
            return result.data[0]

        # try display name next
        result = db.table("users").select("id, email, display_name").eq("display_name", query).limit(1).execute()
        if result.data:
            return result.data[0]

        # IDs are checked last so a display name that looks like a UUID still wins
        if _is_uuid(query):
            result = db.table("users").select("id, email, display_name").eq("id", query).limit(1).execute()
            if result.data:
                return result.data[0]

        return None

    @staticmethod
    def list_all_users():
        # return every user row for the admin users page
        db = _admin_db()
        result = db.table("users").select("id, email, display_name, is_admin").execute()
        if result.data:
            return result.data
        return []

    @staticmethod
    def toggle_user_admin(userId):
        db = _admin_db()

        # look up the current admin flag for this user
        current = db.table("users").select("is_admin").eq("id", userId).limit(1).execute()
        if not current.data:
            return None

        oldVal = current.data[0].get("is_admin", False)

        # flip the value
        if oldVal:
            newVal = False
        else:
            newVal = True

        db.table("users").update({"is_admin": newVal}).eq("id", userId).execute()
        log_event("INFO", "admin", "admin toggled is_admin on user " + str(userId) + " to " + str(newVal), userId=userId)
        return newVal

    @staticmethod
    def list_externals_for_user(userId):
        # return all external calendar rows linked to this user
        db = _admin_db()
        result = db.table("externals").select("id, provider, url").eq("user_id", userId).execute()
        if result.data:
            return result.data
        return []

    @staticmethod
    def unlink_all_external_calendars(userId: str) -> Any:
        # delete every external calendar row for this user
        db = _admin_db()
        result = db.table("externals").delete().eq("user_id", userId).execute()
        log_event("INFO", "admin", "admin unlinked all externals for user " + str(userId), userId=userId)
        return result

    @staticmethod
    def unlink_external_by_id(externalId):
        db = _admin_db()

        # look up the owner so External.remove can keep its cleanup behavior
        lookup = db.table("externals").select("id, user_id").eq("id", externalId).limit(1).execute()
        if not lookup.data:
            return False

        ownerId = lookup.data[0].get("user_id")
        ext = External(id=externalId, supabaseClient=db, userId=ownerId)
        ext.remove(externalId)
        log_event("INFO", "admin", "admin unlinked external " + str(externalId), userId=ownerId)
        return True
