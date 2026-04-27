import os
from supabase import create_client

_logger_client = None


def get_logger_client():
    global _logger_client
    if _logger_client is not None:
        return _logger_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_API_KEY")
    if not url or not key:
        return None
    _logger_client = create_client(url, key)
    return _logger_client


# this function logs stuff to the supabase logs table
# call it from anywhere in the app
def logEvent(level, eventType, message, userId=None, path=None, method=None, statusCode=None, details=None):
    # put all the data into a dict so we can insert it
    # keys have to match the column names in supabase (snake_case)
    logRecord = {}
    logRecord["level"] = level           # INFO WARNING or ERROR
    logRecord["event_type"] = eventType  # what kind of log is this
    logRecord["message"] = message       # the actual log message
    logRecord["user_id"] = userId        # who did the thing (can be None)
    logRecord["path"] = path             # url path if applicable
    logRecord["method"] = method         # http method if applicable
    logRecord["status_code"] = statusCode
    logRecord["details"] = details       # any extra info

    # now try to insert into supabase
    try:
        supabase = get_logger_client()
        if supabase is None:
            print("WARNING: SUPABASE_SECRET_API_KEY not set, skipping log")
            return
        result = supabase.table("logs").insert(logRecord).execute()
        # print(result)
    except Exception as err:
        # if supabase is down or something went wrong just print it
        # we dont want the logging to crash the actual request
        print("WARNING: could not save log to supabase - " + str(err))
        print("log was: [" + str(level) + "] " + str(eventType) + " - " + str(message))
