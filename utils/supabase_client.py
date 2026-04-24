import os
from supabase import create_client

_client = None


def get_supabase_client():
    global _client
    if _client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_API_KEY")
        _client = create_client(supabase_url, supabase_key)
    return _client
