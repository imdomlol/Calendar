import os
from supabase import create_client

# keep a single shared client so we don't reconnect on every request
_client = None


# returns the Supabase client, creating it once if it doesn't exist yet
def get_supabase_client():
    global _client

    if _client is None:
        # grab credentials from environment
        supabaseUrl = os.getenv("SUPABASE_URL")
        supabaseKey = os.getenv("SUPABASE_SECRET_API_KEY")

        # build the client using the service role key so it bypasses RLS
        _client = create_client(supabaseUrl, supabaseKey)

    return _client
