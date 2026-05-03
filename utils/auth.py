import json
import os
from functools import wraps
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import abort, g, request
from utils.logger import log_event


# ========================= Auth Decorator =========================

# wraps any route that needs a logged in user
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # pull the bearer token out of the authorization header
        authHeader = request.headers.get("Authorization", "")
        token = authHeader.removeprefix("Bearer ")
        token = token.strip()

        if not token:
            log_event("WARNING", "auth", "missing token", path=request.path, method=request.method)
            abort(401)

        # grab the Supabase URL and anon key from env
        supabaseUrl = os.environ.get("SUPABASE_URL") or ""
        supabaseUrl = supabaseUrl.rstrip("/")
        supabaseKey = os.environ.get("SUPABASE_KEY") or ""

        # bail early if either env var is missing
        if not supabaseUrl or not supabaseKey:
            abort(500)

        # build a request to ask Supabase who owns this token
        req = Request(
            f"{supabaseUrl}/auth/v1/user",
            headers={
                "apikey": supabaseKey,
                "Authorization": f"Bearer {token}",
            },
            method="GET",
        )

        try:
            with urlopen(req, timeout=15) as response:
                # getcode is a fallback for older urllib versions that don't have .status
                if hasattr(response, "status"):
                    status = response.status
                else:
                    status = response.getcode()

                # anything outside the 2xx range means Supabase rejected the token
                if status < 200 or status >= 300:
                    log_event("WARNING", "auth", "token rejected by supabase", path=request.path, method=request.method)
                    abort(401)

                rawBytes = response.read()
                raw = rawBytes.decode("utf-8")

                if not raw:
                    raw = "{}"
                user = json.loads(raw)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            # any network or parse error counts as a failed validation
            log_event("WARNING", "auth", "token validation failed", path=request.path, method=request.method)
            abort(401)

        # make sure Supabase actually returned a user with a real id
        if not isinstance(user, dict) or not user.get("id"):
            log_event("WARNING", "auth", "token has no user id", path=request.path, method=request.method)
            abort(401)

        # copy id into sub
        if "sub" not in user:
            user["sub"] = user["id"]

        g.user = user
        log_event("INFO", "auth", "token valid", userId=user["id"], path=request.path, method=request.method)

        return f(*args, **kwargs)

    return decorated
