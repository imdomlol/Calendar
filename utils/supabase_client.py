import os
from supabase import create_client


def get_supabase_client():
    # get the url and key from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    # create the client and return it
    return create_client(supabase_url, supabase_key)
