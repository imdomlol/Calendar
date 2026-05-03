import os
from supabase import create_client

_loggerClient = None


# ========================= Supabase Client =========================


# get the cached logging client if we already made one
def get_logger_client():
    global _loggerClient
    if _loggerClient is not None:
        return _loggerClient

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_API_KEY")

    # logging cannot work without both supabase values
    if not url or not key:
        return None

    _loggerClient = create_client(url, key)
    return _loggerClient


# ========================= Event Logging =========================


# save one app event in the supabase logs table
def log_event(level, eventType, message, userId=None, path=None, method=None, statusCode=None, details=None):
    # build the row with the column names supabase expects
    logRecord = {}
    logRecord["level"] = level
    logRecord["event_type"] = eventType
    logRecord["message"] = message
    logRecord["user_id"] = userId
    logRecord["path"] = path
    logRecord["method"] = method
    logRecord["status_code"] = statusCode
    logRecord["details"] = details

    # try to send the log without breaking the real request
    try:
        supabaseClient = get_logger_client()
        if supabaseClient is None:
            print("WARNING: SUPABASE_SECRET_API_KEY not set, skipping log")
            return

    except Exception as error:
        # logging errors should show in the server output
        print("WARNING: could not save log to supabase - " + str(error))
        print("log was: [" + str(level) + "] " + str(eventType) + " - " + str(message))
