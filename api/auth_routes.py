from flask import Blueprint, request
import os

from utils.supabase_client import get_supabase_client
from utils.logger import logEvent

auth_bp = Blueprint("auth", __name__)
supabase = get_supabase_client()


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        # get the json body from the request
        # silent=True means it wont throw an error if the body is missing or not json
        reqBody = request.get_json(silent=True) or {}
        # pull out the fields we need from the body
        email = reqBody.get("email")
        password = reqBody.get("password")
        name = reqBody.get("name") #name is optional

        # check that email and password are both there and not empty
        # we store the results in variables first so its easier to read
        emailOk = email is not None and len(email) > 0
        pwOk = password is not None and len(password) > 0
        if not emailOk or not pwOk:
            return {"error": "email and password are required"}, 400

        # get the base url so we can build the email verification redirect link
        # first we check if the environment variable is set
        baseUrl = (os.environ.get("APP_BASE_URL") or "").strip().rstrip("/")
        # if there is no env var we fall back to whatever the current request root is
        if not baseUrl:
            baseUrl = request.url_root.rstrip("/")

        # build the payload dict to send to supabase
        # this has the email password and options like the redirect url
        payload = {
            "email": email,
            "password": password,
            "options": {
                "email_redirect_to": f"{baseUrl}/ui/login",
            },
        }
        # if name was provided we add it to the options data
        if name:
            payload["options"]["data"] = {"name": name}

        # call supabase to create the account
        result = supabase.auth.sign_up(payload)
        logEvent("INFO", "auth", "user registered", details="email: " + email)

        # return the new user and session info
        # 201 means something was created
        return {
            "message": "User created",
            "session": result.session,
            "user": result.user,
        }, 201

    except Exception as e:
        logEvent("ERROR", "auth", "registration failed", details="email: " + str(email) + " error: " + str(e))
        return {"error": str(e)}, 500




@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    email = d.get("email")
    pw = d.get("password")

    if len(email or "") == 0 or len(pw or "") == 0:
        return {"error": "email and password are required"}, 400

    try:
        res = supabase.auth.sign_in_with_password(
            {"email": email, "password": pw}
        )
        userId = getattr(res.user, "id", None)
        logEvent("INFO", "auth", "login successful", userId=userId, details="email: " + email)
        return {
            "message": "Login successful",
            "session": res.session,
            "user": res.user,
        }, 200
    except Exception:
        logEvent("WARNING", "auth", "login failed - bad credentials", details="email: " + str(email))
        return {"error": "Invalid credentials"}, 401
