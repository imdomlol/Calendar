import os
from supabase import create_client

# keep a single shared client so we don't reconnect on every request
_client = None
_anon_client = None


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


# returns a client using the anon key — must be used for auth operations so
# Supabase enforces email confirmation (service role key bypasses it)
def get_anon_supabase_client():
    global _anon_client

    if _anon_client is None:
        supabaseUrl = os.getenv("SUPABASE_URL")
        supabaseKey = os.getenv("SUPABASE_KEY")
        _anon_client = create_client(supabaseUrl, supabaseKey)

    return _anon_client
