#this testing file is completely AI generated, and is not meant to be a real test. It is meant to be a placeholder for future tests, and to demonstrate how to use the Supabase client. It may contain errors or incomplete code, and should not be used as a reference for real tests.
# - dom

import os
import sys
from importlib import import_module


def get_supabase_client():
	try:
		load_dotenv = import_module("dotenv").load_dotenv
		load_dotenv()
	except ModuleNotFoundError:
		pass

	try:
		create_client = import_module("supabase").create_client
	except ModuleNotFoundError as exc:
		raise RuntimeError(
			"Missing package 'supabase' for interpreter "
			f"{sys.executable}. Use '.venv/bin/python -m pip install supabase' "
			"and run scripts with '.venv/bin/python ...'."
		) from exc

	supabase_url = os.getenv("SUPABASE_URL")
	supabase_key = os.getenv("SUPABASE_KEY")
	typo_key = os.getenv("SUPABSE_KEY")

	if not supabase_url or not supabase_key:
		message = "Missing SUPABASE_URL or SUPABASE_KEY environment variables."
		if typo_key and not supabase_key:
			message += " Found SUPABSE_KEY; did you mean SUPABASE_KEY?"
		raise RuntimeError(message)

	return create_client(supabase_url, supabase_key)
