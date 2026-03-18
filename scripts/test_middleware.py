# this testing file is completely AI generated, and is not meant to be a real test. It is meant to be a placeholder for future tests, and to demonstrate how to use the Supabase client. It may contain errors or incomplete code, and should not be used as a reference for real tests.
# - dom

import os
import json
import sys
from importlib import import_module
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from flask import Flask, g

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    load_dotenv = import_module("dotenv").load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except ModuleNotFoundError:
    pass

from utils.auth import require_auth


def build_test_app() -> Flask:
    app = Flask(__name__)

    @app.route("/protected", methods=["GET"])
    @require_auth
    def protected() -> tuple[dict, int]:
        user = getattr(g, "user", {})
        return {
            "message": "Authorized",
            "user_id": user.get("sub"),
            "role": user.get("role"),
        }, 200

    return app


def auth_request(path: str, payload: dict) -> tuple[int, dict]:
    base_url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    api_key = os.getenv("SUPABASE_KEY") or ""

    if not base_url or not api_key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY before running this script.")

    url = f"{base_url}/auth/v1/{path.lstrip('/')}"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")

    try:
        request = Request(url, data=data, headers=headers, method="POST")
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body) if body else {}
            return response.getcode(), parsed
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        parsed = {}
        if body:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body}
        return exc.code, parsed


def sign_in_with_password(email: str, password: str) -> str | None:
    signin_status, signin_body = auth_request(
        "token?grant_type=password",
        {"email": email, "password": password},
    )
    if signin_status not in (200, 201):
        message = signin_body.get("msg") or signin_body.get("error_description") or signin_body.get("error") or signin_body
        print("Sign-in failed:", message)
        return None

    if signin_body.get("access_token"):
        return signin_body.get("access_token")

    return None


def main() -> int:
    existing_email = (os.getenv("SUPABASE_TEST_EXISTING_EMAIL") or "").strip()
    existing_password = (os.getenv("SUPABASE_TEST_EXISTING_PASSWORD") or "").strip()

    if not existing_email or not existing_password:
        print("Set SUPABASE_TEST_EXISTING_EMAIL and SUPABASE_TEST_EXISTING_PASSWORD.")
        return 1

    print("Signing in existing user:", existing_email)

    try:
        access_token = sign_in_with_password(existing_email, existing_password)
    except Exception as exc:
        print("Auth request failed:", str(exc))
        return 1

    if not access_token:
        print("Could not obtain an access token from existing credentials.")
        return 1

    app = build_test_app()
    client = app.test_client()

    unauthorized = client.get("/protected")
    if unauthorized.status_code != 401:
        print("Expected 401 without token, got:", unauthorized.status_code)
        return 1

    authorized = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if authorized.status_code != 200:
        print("Expected 200 with valid token, got:", authorized.status_code)
        print("Response body:", authorized.get_data(as_text=True))
        print("Middleware rejected a token that sign-in accepted.")
        return 1

    payload = authorized.get_json(silent=True) or {}
    print("Middleware authorized user id:", payload.get("user_id"))
    print("Middleware session test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
