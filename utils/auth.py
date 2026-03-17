from functools import wraps
from flask import request, abort
import os

def require_auth(f):
    @wraps(f) # helps preserve function metadata
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token or token != os.environ.get("API_SECRET"): # dont forget to set in vercel
            abort(401)
        return f(*args, **kwargs)
    return decorated