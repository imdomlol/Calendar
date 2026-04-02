import json
import os
from functools import wraps
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import abort, g, request

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # grab the token from the header.
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            abort(401)

        # supabase project URL + key are required to validate
        supabase_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
        supabase_key = os.environ.get("SUPABASE_KEY") or ""
        if not supabase_url or not supabase_key:
            abort(500)

        # ask supabase who this token belongs to
        req = Request(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {token}",
            },
            method="GET",
        )

        try:
            with urlopen(req, timeout=15) as response:
                status = getattr(response, "status", response.getcode())
                if status < 200 or status >= 300:
                    abort(401)
                raw = response.read().decode("utf-8")
                user = json.loads(raw or "{}")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            abort(401)

        # if supabase does not return a real user id, treat it as unauthorized
        if not isinstance(user, dict) or not user.get("id"):
            abort(401)

        user.setdefault("sub", user["id"])
        g.user = user

        return f(*args, **kwargs)

    return decorated