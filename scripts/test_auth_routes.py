import os
import sys
import types
from importlib import import_module
from pathlib import Path
from uuid import uuid4

from flask import Flask


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _load_env_file_fallback(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            os.environ[key] = value

try:
    load_dotenv = import_module("dotenv").load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
except ModuleNotFoundError:
    _load_env_file_fallback(PROJECT_ROOT / ".env")


def _load_auth_blueprint():
    real_get_supabase_client = import_module("utils.supabase_client").get_supabase_client
    real_client = real_get_supabase_client()

    stub_module = types.ModuleType("supabase_client")
    stub_module.get_supabase_client = lambda: real_client
    sys.modules["supabase_client"] = stub_module

    auth_routes = import_module("api.auth_routes")
    auth_routes.supabase = real_client
    return auth_routes.auth_bp


def _check_env() -> int:
    required = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print("Missing required environment variable(s):", ", ".join(missing))
        return 1
    return 0


def main() -> int:
    env_status = _check_env()
    if env_status != 0:
        return env_status

    auth_bp = _load_auth_blueprint()

    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    client = app.test_client()

    test_email = f"route-test-{uuid4().hex[:10]}@example.com"
    test_password = "RouteTest!12345"

    register_response = client.post(
        "/register",
        json={
            "email": test_email,
            "password": test_password,
            "display_name": "Route Tester",
        },
    )
    if register_response.status_code != 201:
        print("/register failed:", register_response.status_code, register_response.get_data(as_text=True))
        return 1

    register_payload = register_response.get_json(silent=True) or {}
    if not register_payload.get("user"):
        print("/register failed: missing user payload")
        return 1

    login_response = client.post(
        "/login",
        json={
            "email": test_email,
            "password": test_password,
        },
    )
    if login_response.status_code != 200:
        print("/login failed:", login_response.status_code, login_response.get_data(as_text=True))
        return 1

    login_payload = login_response.get_json(silent=True) or {}
    if not login_payload.get("session"):
        print("/login failed: missing session payload")
        return 1

    invalid_login_response = client.post(
        "/login",
        json={
            "email": test_email,
            "password": "wrong-password",
        },
    )
    if invalid_login_response.status_code != 401:
        print(
            "Expected invalid credentials to return 401, got:",
            invalid_login_response.status_code,
            invalid_login_response.get_data(as_text=True),
        )
        return 1

    print(f"Created Supabase test account: {test_email}")
    print("Auth route tests passed: /register and /login behave as expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())