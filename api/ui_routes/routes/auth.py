from flask import redirect, request, session, url_for
from api.ui_routes import ui_bp

from api.ui_routes.helpers import (
    _format_login_error,
    guest_nav,
    render_page,
    _resolve_app_base_url,
)
from utils.supabase_client import get_supabase_client


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    info = (request.args.get("info") or "").strip()
    nextPath = (request.args.get("next") or "").strip() or url_for("ui.dashboard", role="user")
    # only allow relative paths to stop open redirects
    if not nextPath.startswith("/"):
        nextPath = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        # check if email or password is empty
        # if either one is empty we cant log in
        if len(email) == 0 or len(password) == 0:
            error = "Email and password are required."
        else:
            try:
                sb = get_supabase_client()
                result = sb.auth.sign_in_with_password({"email": email, "password": password})
                # supabase returns objects not plain dicts so we use getattr
                user_obj = getattr(result, "user", None)
                session_obj = getattr(result, "session", None)
                uid = getattr(user_obj, "id", None)
                access_token = getattr(session_obj, "access_token", None)
                has_uid = uid is not None
                if has_uid == False:
                    error = "Login failed."
                else:
                    session["ui_user"] = {
                        "id": uid,
                        "email": getattr(user_obj, "email", email),
                        "access_token": access_token,
                    }
                    return redirect(nextPath)
            except Exception as exc:
                error = _format_login_error(exc)

    return render_page("Log In", "guest", guest_nav(), "auth/login.html",
                       error=error, info=info, next_path=nextPath)






@ui_bp.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    next_path = (request.args.get("next") or "").strip() or url_for("ui.dashboard", role="user")
    if not next_path.startswith("/"):
        next_path = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not email or not password:
            error = "Email and password are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            try:
                supabase = get_supabase_client()
                app_base_url = _resolve_app_base_url()
                options = {"email_redirect_to": f"{app_base_url}{url_for('ui.login')}"}
                if name:
                    options["data"] = {"name": name}
                supabase.auth.sign_up({"email": email, "password": password, "options": options})
                return redirect(url_for(
                    "ui.login",
                    next=next_path,
                    info=(
                        "Account created. Please check your email to verify your account "
                        "before logging in."
                    ),
                ))
            except Exception as exc:
                error = f"Could not register: {exc}"

    return render_page("Register", "guest", guest_nav(), "auth/register.html",
                       error=error, next_path=next_path)

@ui_bp.route("/logout")
def logout():
    # this function logs the user out
    # we do this by removing the user from the flask session
    # session is where flask stores info about who is logged in
    # session.pop removes the key called ui_user from the session
    # if ui_user isnt there it just does nothing because of the None default
    session.pop("ui_user", None)
    # now we need to send the user to the home page
    # they are logged out so home makes sense
    homeUrl = url_for("ui.home") #get url for the home page
    return redirect(homeUrl)
