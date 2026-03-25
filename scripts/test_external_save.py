#this testing file is completely AI generated, and is not meant to be a real test. It is meant to be a placeholder for future tests, and to demonstrate how to use the Supabase client. It may contain errors or incomplete code, and should not be used as a reference for real tests.
# - dom

import os
import sys
from importlib import import_module
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    load_dotenv = import_module("dotenv").load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except ModuleNotFoundError:
    pass

from models.external import External
from utils.supabase_client import get_supabase_client


def check_env() -> int:
    required = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing = []

    for key in required:
        value = os.getenv(key)
        if value:
            print(f"{key}=set")
        else:
            print(f"{key}=missing")
            missing.append(key)

    if missing:
        return 1

    print("Environment variables look good.")
    return 0


def main() -> int:
    if "--check-env" in sys.argv:
        return check_env()

    try:
        supabase = get_supabase_client()
    except RuntimeError as exc:
        message = str(exc)
        print(message)
        if "SUPABASE_URL" in message or "SUPABASE_KEY" in message:
            print("Set SUPABASE_URL and SUPABASE_KEY, then rerun the script.")
        elif "Missing package 'supabase'" in message:
            print("Run: .venv/bin/python -m pip install supabase")
        return 1

    external = External(
        id=f"{uuid4()}",
        url="https://example.com/calendar",
        provider="manual",
        supabase_client=supabase,
        user_id=f"{uuid4()}",
        access_token=f"{uuid4()}",
        refresh_token=f"-{uuid4()}",
        owner_id=f"{uuid4()}",
    )

    if external.id is None:
        external.id = str(uuid4())

    insert_result = external.save()

    if not insert_result.data:
        print("Insert failed: no data returned")
        return 1

    print("Inserted external id:", external.id)

    fetched = (
        supabase.table("externals")
        .select("id, url, provider, user_id, access_token, refresh_token, owner_id")
        .eq("id", external.id)
        .single()
        .execute()
    )

    if not fetched.data:
        print("Read-back failed: could not find inserted external")
        return 1

    print("Read-back row:", fetched.data)

    if os.getenv("CLEANUP_TEST_ROW") == "1":
        supabase.table("externals").delete().eq("id", external.id).execute()
        print("Cleanup complete: deleted test row")

    print("External save test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
