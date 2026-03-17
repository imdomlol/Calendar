from functools import wraps
from flask import request, abort, g
import os
import jwt

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")

def require_auth(f):
    @wraps(f) # Preserve function metadata
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            abort(401)
        try:
            # Decode the JWT token to get user info
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
            g.user = payload  # current session available everywhere
        except jwt.ExpiredSignatureError:
            abort(401)
        except jwt.InvalidTokenError:
            abort(401)
        return f(*args, **kwargs)
    return decorated