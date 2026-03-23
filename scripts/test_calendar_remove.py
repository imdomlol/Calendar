#this testing file is completely AI generated, and is not meant to be a real test. It is meant to be a placeholder for future tests, and to demonstrate how to use the Supabase client. It may contain errors or incomplete code, and should not be used as a reference for real tests.
# - dom

import os
import sys
from importlib import import_module
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

try:
	load_dotenv = import_module("dotenv").load_dotenv
	load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except ModuleNotFoundError:
	pass

from models.calendar import Calendar
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

	fetched = (
		supabase.table("calendars")
		.select("id, name, owner_id, member_ids, events, age_timestamp")
		.order("age_timestamp", desc=False)
		.limit(1)
		.execute()
	)

	rows = fetched.data or []
	if not rows:
		print("No calendars found to remove.")
		return 1

	row = rows[0]
	calendar = Calendar(
		name=row.get("name") or "Untitled Calendar",
		owner_id=row.get("owner_id") or "",
	)
	calendar.id = row.get("id")
	calendar.member_ids = row.get("member_ids") or [calendar.owner_id]
	calendar.events = row.get("events") or []
	calendar.age_timestamp = row.get("age_timestamp")

	if not calendar.id:
		print("First row is missing an id; cannot remove calendar")
		return 1

	print("Removing calendar id:", calendar.id)
	print("Calendar row:", row)

	remove_result = calendar.remove_calendar()

	if remove_result.data:
		print("Removed row:", remove_result.data)
	else:
		print("Remove executed (no row payload returned).")

	print("Calendar remove test passed")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
