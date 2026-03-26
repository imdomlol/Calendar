#this testing file is completely AI generated, and is not meant to be a real test. It is meant to be a placeholder for future tests, and to demonstrate how to use the Supabase client. It may contain errors or incomplete code, and should not be used as a reference for real tests.
# - dom

import os
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    load_dotenv = import_module("dotenv").load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
except ModuleNotFoundError:
    pass

from models.calendar import Calendar


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

    calendar = Calendar(
        name="Integration Test Calendar",
        owner_id=str(uuid4()),
    )

    calendar.add_event(str(uuid4()))

    # Keep the test compatible even if Calendar.save() does not auto-populate fields yet.
    if calendar.id is None:
        calendar.id = str(uuid4())
    if calendar.age_timestamp is None:
        calendar.age_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        insert_result = calendar.save()
    except RuntimeError as exc:
        message = str(exc)
        print(message)
        if "SUPABASE_URL" in message or "SUPABASE_KEY" in message:
            print("Set SUPABASE_URL and SUPABASE_KEY, then rerun the script.")
        elif "Missing package 'supabase'" in message:
            print("Run: .venv/bin/python -m pip install supabase")
        return 1

    if not insert_result.data:
        print("Insert failed: no data returned")
        return 1

    print("Inserted calendar id:", calendar.id)
    print("Generated age_timestamp:", calendar.age_timestamp)

    from utils.supabase_client import get_supabase_client

    supabase = get_supabase_client()
    fetched = (
        supabase.table("calendars")
        .select("id, name, owner_id, member_ids, events, age_timestamp")
        .eq("id", calendar.id)
        .single()
        .execute()
    )

    if not fetched.data:
        print("Read-back failed: could not find inserted calendar")
        return 1

    print("Read-back row:", fetched.data)

    if os.getenv("CLEANUP_TEST_ROW") == "1":
        supabase.table("calendars").delete().eq("id", calendar.id).execute()
        print("Cleanup complete: deleted test row")

    print("Calendar save test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
