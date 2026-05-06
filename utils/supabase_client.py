import os
from supabase import create_client

# keep a single shared client so we don't reconnect on every request
_client = None
_auth_client = None


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


# returns an anon-key client used only for auth operations (sign_in, sign_up).
# supabase-py v2 overwrites the PostgREST Authorization header on SIGNED_IN events,
# so auth operations must never share the service-role singleton.
def get_auth_client():
    global _auth_client

    if _auth_client is None:
        supabaseUrl = os.getenv("SUPABASE_URL")
        supabaseKey = os.getenv("SUPABASE_KEY")
        _auth_client = create_client(supabaseUrl, supabaseKey)

    return _auth_client
