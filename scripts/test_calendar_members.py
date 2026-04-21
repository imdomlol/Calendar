# Test script for Calendar class add_member and remove_member functions
# This script tests the functionality of adding and removing members from a calendar.
# It creates a test calendar and user, performs the operations, and cleans up.

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
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except ModuleNotFoundError:
    pass

from models.calendar import Calendar, InvalidUserID
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


def create_test_user(supabase) -> str:
    """Create a test user in the database and return the user ID."""
    user_id = str(uuid4())
    user_data = {
        "id": user_id,
        "display_name": "Test User",
        "email": "test@example.com",
        "calendars": [],
        "events": [],
        "externals": []
    }
    result = supabase.table("users").insert(user_data).execute()
    if not result.data:
        raise RuntimeError("Failed to create test user")
    print(f"Created test user with ID: {user_id}")
    return user_id


def delete_test_user(supabase, user_id: str):
    """Delete the test user from the database."""
    supabase.table("users").delete().eq("id", user_id).execute()
    print(f"Deleted test user with ID: {user_id}")


def main() -> int:
    if "--check-env" in sys.argv:
        return check_env()

    supabase = get_supabase_client()

    # Create test user
    try:
        test_user_id = create_test_user(supabase)
    except Exception as e:
        print(f"Failed to create test user: {e}")
        return 1

    # Create and save test calendar
    calendar = Calendar(
        name="Test Calendar for Members",
        owner_id=str(uuid4()),  # Random owner ID
    )
    calendar.id = str(uuid4())
    calendar.age_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        insert_result = calendar.save()
        if not insert_result.data:
            print("Failed to save test calendar")
            delete_test_user(supabase, test_user_id)
            return 1
        print(f"Created test calendar with ID: {calendar.id}")
    except Exception as e:
        print(f"Failed to save calendar: {e}")
        delete_test_user(supabase, test_user_id)
        return 1

    # Test add_member
    print("\n--- Testing add_member ---")

    # Test adding a valid member
    try:
        result = calendar.add_member(test_user_id)
        print(f"Successfully added member {test_user_id}. Result: {result}")
    except InvalidUserID as e:
        print(f"Unexpected error adding valid member: {e}")
        return 1
    except Exception as e:
        print(f"Error adding member: {e}")
        return 1

    # Test adding the owner (should fail)
    try:
        calendar.add_member(calendar.owner_id)
        print("ERROR: Should not be able to add owner as member")
        return 1
    except InvalidUserID as e:
        print(f"Correctly prevented adding owner: {e}")

    # Test adding already existing member
    try:
        result = calendar.add_member(test_user_id)
        print(f"Attempted to add existing member: {result}")
    except Exception as e:
        print(f"Error adding existing member: {e}")

    # Test adding non-existent user
    fake_user_id = str(uuid4())
    try:
        calendar.add_member(fake_user_id)
        print("ERROR: Should not be able to add non-existent user")
        return 1
    except ValueError as e:
        print(f"Correctly prevented adding non-existent user: {e}")

    # Test remove_member
    print("\n--- Testing remove_member ---")

    # Test removing a valid member
    try:
        result = calendar.remove_member(test_user_id)
        print(f"Successfully removed member {test_user_id}. Result: {result}")
    except Exception as e:
        print(f"Error removing member: {e}")
        return 1

    # Test removing non-existent member
    try:
        calendar.remove_member(fake_user_id)
        print("ERROR: Should not be able to remove non-existent member")
        return 1
    except KeyError as e:
        print(f"Correctly prevented removing non-existent member: {e}")

    # Cleanup
    print("\n--- Cleanup ---")
    try:
        supabase.table("calendars").delete().eq("id", calendar.id).execute()
        print("Deleted test calendar")
        delete_test_user(supabase, test_user_id)
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return 1

    print("All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())