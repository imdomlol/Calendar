from flask import redirect, request, session, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _format_login_error,
    render_page,
    _resolve_app_base_url,
)
from utils.supabase_client import get_supabase_client
from utils.logger import log_event


# ========================= Login Routes =========================


# show the login form or handle a submitted login
@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    # grab the info message from the url if there is one
    info = (request.args.get("info") or "").strip()

    # figure out where to send the user after login
    # check the next param first and fall back to the dashboard
    nextPath = (
        (request.args.get("next") or "").strip()
        or url_for("ui.dashboard", role="user")
    )

    # only allow relative paths to stop redirects
    if not nextPath.startswith("/"):
        nextPath = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if len(email) == 0 or len(password) == 0:
            error = "Email and password are required"
        else:
            try:
                calDb = get_supabase_client()

                # send the credentials to Supabase
                result = calDb.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )

                # Supabase returns objects not plain dicts
                userObj = getattr(result, "user", None)
                sessObj = getattr(result, "session", None)
                uid = getattr(userObj, "id", None)
                accessTok = getattr(sessObj, "access_token", None)

                # check if we got a real user back
                hasUid = uid is not None
                if not hasUid:
                    log_event(
                        "WARNING",
                        "auth",
                        "login failed - no uid returned",
                        details="email: " + email,
                    )
                    error = "Wrong email or password"
                else:
                    # look up suspension and admin flags from the users table
                    isAdmin = False
                    isSuspended = False
                    try:
                        userQuery = calDb.table("users")
                        userQuery = userQuery.select("is_admin, is_suspended, display_name")
                        userQuery = userQuery.eq("id", uid)
                        userResult = userQuery.limit(1).execute()

                        if userResult.data:
                            userRow = userResult.data[0]
                            isAdmin = bool(userRow.get("is_admin", False))
                            isSuspended = bool(userRow.get("is_suspended", False))

                            # sync display_name from auth metadata if the public row is missing it
                            if not userRow.get("display_name"):
                                userMeta = getattr(userObj, "user_metadata", {}) or {}
                                authName = userMeta.get("name") or userMeta.get("full_name")
                                if authName:
                                    calDb.table("users").update({"display_name": authName}).eq("id", uid).execute()
                    except Exception:
                        # dont block login if the flags lookup fails
                        pass

                    if isSuspended:
                        session.pop("ui_user", None)
                        log_event(
                            "WARNING",
                            "auth",
                            "Suspended account",
                            userId=uid,
                            details="email: " + email,
                        )
                        error = "Your account has been suspended"
                    else:
                        # store the user info in the session so requests know who they are
                        session["ui_user"] = {
                            "id": uid,
                            "email": getattr(userObj, "email", email),
                            "access_token": accessTok,
                            "is_admin": isAdmin,
                        }
                        log_event(
                            "INFO",
                            "auth",
                            "login successful",
                            userId=uid,
                            details="email: " + email,
                        )

                        return redirect(nextPath)
            except Exception as loginErr:
                # turn the exception into something the user can read
                log_event(
                    "WARNING",
                    "auth",
                    "login failed - exception",
                    details="email: " + email + " error: " + str(loginErr),
                )
                error = _format_login_error(loginErr)

    return render_page(
        "Log In",
        "auth/login.html",
        error=error,
        info=info,
        next_path=nextPath,
        hide_chrome=True,
    )


# ========================= Registration Routes =========================


# show the registration form or create a new account
@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None

    nextPath = (
        (request.args.get("next") or "").strip()
        or url_for("ui.dashboard", role="user")
    )

    # same redirect safety check as login
    if not nextPath.startswith("/"):
        nextPath = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # second password field so the user can confirm they typed it right
        confirmPwd = request.form.get("confirm_password") or ""

        if len(email) == 0 or len(password) == 0:
            error = "Email and password are required."
        elif password != confirmPwd:
            error = "PASSWORDS DON'T MATCH"
        else:
            try:
                calDb = get_supabase_client()
                appBaseUrl = _resolve_app_base_url()

                # build the signup options and set where Supabase should redirect after email confirmation
                options = {"email_redirect_to": f"{appBaseUrl}{url_for('ui.login')}"}

                if name:
                    options["data"] = {"name": name}

                calDb.auth.sign_up(
                    {"email": email, "password": password, "options": options}
                )
                log_event(
                    "INFO",
                    "auth",
                    "user registered",
                    details="email: " + email,
                )

                # account created so send them to login WITH a email link message
                return redirect(
                    url_for(
                        "ui.login",
                        next=nextPath,
                        info=(
                            "Account created. Please check your email to verify your account "
                            "before logging in."
                        ),
                    )
                )
            except Exception as err:
                log_event(
                    "ERROR",
                    "auth",
                    "registration failed",
                    details="email: " + email + " error: " + str(err),
                )
                error = f"signup failed for {email}: {err}"

    return render_page(
        "Register",
        "auth/register.html",
        error=error,
        next_path=nextPath,
        hide_chrome=True,
    )


# ========================= Logout Routes =========================


# clear the session and redirect to the home page
@ui_bp.route("/logout")
def logout():
    session.pop("ui_user", None)

    homeUrl = url_for("ui.home")
    return redirect(homeUrl)
