import os
import sys
from importlib import import_module


def get_supabase_client():
	try:
		create_client = import_module("supabase").create_client
	except ModuleNotFoundError as exception:
		raise RuntimeError(
			"Missing package 'supabase' for interpreter "
			f"{sys.executable}. Use '.venv/bin/python -m pip install supabase' "
			"and run scripts with '.venv/bin/python ...'."
		) from exception

	supabase_url = os.getenv("SUPABASE_URL")
	supabase_key = os.getenv("SUPABASE_KEY")

	if not supabase_url or not supabase_key:
		message = "Missing required environment variables."
		raise RuntimeError(message)

	return create_client(supabase_url, supabase_key)
