from flask import redirect, request, session, url_for
from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _format_login_error,
    guest_nav,
    render_page,
    _resolve_app_base_url,
)
from utils.supabase_client import get_supabase_client
from utils.logger import logEvent


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    # if something goes wrong we put the message here
    error = ""
    # get the info message from the url if there is one
    info = (request.args.get("info") or "").strip()
    # figure out where to send the user after login
    # we check the next param first and fall back to dashboard
    nextPath = (
        (request.args.get("next") or "").strip()
        or url_for("ui.dashboard", role="user")
    )
    # only allow relative paths to stop open redirects
    # if the path doesnt start with / we dont trust it
    if not nextPath.startswith("/"):
        nextPath = url_for("ui.dashboard", role="user")

    # check if the request is a form submission
    if request.method == "POST":
        # get email and password from the form
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # check if email or password is empty
        # if either one is empty we cant log in
        if len(email) == 0 or len(password) == 0:
            error = "Email and password are required"
        else:
            try:
                # get the supabase client so we can talk to the database
                calDb = get_supabase_client()
                result = calDb.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
                # supabase returns objects not plain dicts so we use getattr
                # getattr lets us safely get attributes without crashing
                user_obj = getattr(result, "user", None)
                sess_obj = getattr(result, "session", None)
                uid = getattr(user_obj, "id", None)
                access_tok = getattr(sess_obj, "access_token", None)
                # check if we got a user id back
                # if uid is None the login didnt work
                has_uid = uid is not None
                if has_uid == False:
                    logEvent("WARNING", "auth", "login failed - no uid returned", details="email: " + email)
                    error = "Wrong email or password"
                else:
                    # read the app_metadata from the user object supabase gave us back
                    # app_metadata is a dict that only admins can write to
                    # so if role is "admin" in here, we know it was set by an admin
                    app_meta = getattr(user_obj, "app_metadata", None)
                    # if app_meta is None (not set at all) use an empty dict so we dont crash
                    if app_meta is None:
                        app_meta = {}
                    # get the role from app_meta, if its not there just use "user" as the default
                    role = app_meta.get("role", "user")

                    # check account flags on the users table
                    is_admin = False
                    is_suspended = False
                    try:
                        user_result = calDb.table("users").select("is_admin, is_suspended").eq("id", uid).limit(1).execute()
                        if user_result.data:
                            user_row = user_result.data[0]
                            is_admin = bool(user_row.get("is_admin", False))
                            is_suspended = bool(user_row.get("is_suspended", False))
                    except Exception:
                        pass

                    if is_suspended:
                        session.pop("ui_user", None)
                        logEvent("WARNING", "auth", "Suspended account", userId=uid, details="email: " + email)
                        error = "Your account has been suspended"
                    else:
                        # save the user info to the flask session
                        # this is how we remember who is logged in between requests
                        session["ui_user"] = {
                            "id": uid,
                            "email": getattr(user_obj, "email", email),
                            "access_token": access_tok,
                            "role": role,
                            "is_admin": is_admin,
                        }
                        logEvent("INFO", "auth", "login successful", userId=uid, details="email: " + email)
                        # send them to wherever they were trying to go
                        return redirect(nextPath)
            except Exception as e:
                logEvent("WARNING", "auth", "login failed - exception", details="email: " + email + " error: " + str(e))
                error = _format_login_error(e)

    # render the login page and pass along any error or info messages
    return render_page(
        "Log In", "guest", guest_nav(), "auth/login.html",
        error=error, info=info, next_path=nextPath, hide_chrome=True,
    )



@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    # no error yet
    error = None
    # get the next path from the url or default to dashboard
    next_path = (
        (request.args.get("next") or "").strip()
        or url_for("ui.dashboard", role="user")
    )
    # make sure the next path is relative so we dont redirect to random sites
    if not next_path.startswith("/"):
        next_path = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        # get all the fields from the registration form
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        # this is the second password field the user types to confirm they typed it right
        confirm_pwd = request.form.get("confirm_password") or ""

        # make sure email and password are not empty
        if len(email) == 0 or len(password) == 0:
            error = "Email and password are required."
        elif password != confirm_pwd:
            # the two passwords the user typed dont match
            error = "PASSWORDS DON'T MATCH"
        else:
            try:
                calDb = get_supabase_client()
                appBaseUrl = _resolve_app_base_url()
                # build the options dict for supabase signup
                # email_redirect_to is where supabase sends the confirmation link
                options = {"email_redirect_to": f"{appBaseUrl}{url_for('ui.login')}"}
                # only add the name if the user actually typed one
                if name:
                    options["data"] = {"name": name}
                calDb.auth.sign_up(
                    {"email": email, "password": password, "options": options}
                )
                logEvent("INFO", "auth", "user registered", details="email: " + email)
                # registration worked so send them to login with a message
                return redirect(url_for(
                    "ui.login",
                    next=next_path,
                    info=(
                        "Account created. Please check your email to verify your account "
                        "before logging in."
                    ),
                ))
            except Exception as err:
                logEvent("ERROR", "auth", "registration failed", details="email: " + email + " error: " + str(err))
                error = f"signup failed for {email}: {err}"

    # show the register page
    return render_page(
        "Register", "guest", guest_nav(), "auth/register.html",
        error=error, next_path=next_path, hide_chrome=True,
    )

@ui_bp.route("/logout")
def logout():
    # remove the user from the session
    # session.pop does nothing if the key isnt there
    session.pop("ui_user", None)
    # get the home page url then redirect there
    homeUrl = url_for("ui.home") #home page url
    return redirect(homeUrl)
