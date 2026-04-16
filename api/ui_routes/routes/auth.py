from html import escape

from flask import redirect, request, session, url_for
from utils.supabase_client import get_supabase_client

from api.ui_routes import ui_bp
from api.ui_routes.helpers import (
    _format_login_error,
    _resolve_app_base_url,
    _ui_user,
    guest_nav,
    render_page,
)


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    info = (request.args.get("info") or "").strip()
    next_path = (request.args.get("next") or "").strip() or url_for("ui.dashboard", role="user")
    if not next_path.startswith("/"):
        next_path = url_for("ui.dashboard", role="user")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            error = "Email and password are required."
        else:
            try:
                supabase = get_supabase_client()
                result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                user_obj = getattr(result, "user", None)
                session_obj = getattr(result, "session", None)
                user_id = getattr(user_obj, "id", None)
                access_token = getattr(session_obj, "access_token", None)
                if not user_id:
                    error = "Login failed."
                else:
                    session["ui_user"] = {
                        "id": user_id,
                        "email": getattr(user_obj, "email", email),
                        "access_token": access_token,
                    }
                    return redirect(next_path)
            except Exception as exc:
                error = _format_login_error(exc)

    error_block = ""
    if error:
        error_block = f"<p style='color:#b91c1c; margin:0 0 12px 0;'>{escape(error)}</p>"

    info_block = ""
    if info and not error:
        info_block = f"<p style='color:#166534; margin:0 0 12px 0;'>{escape(info)}</p>"

    body = f"""
    <div class='hero'>
      <h1>Log In</h1>
      <p class='muted'>Sign in to access user and admin pages.</p>
    </div>
    <div class='card'>
      {info_block}
      {error_block}
      <form method='POST' action='/ui/login?next={escape(next_path)}' style='display:flex; flex-direction:column; gap:10px; max-width:420px;'>
      <input type='email' name='email' placeholder='Email' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='password' placeholder='Password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <button type='submit' class='btn' style='border:none; cursor:pointer; width:max-content; margin-top:0;'>Log In</button>
      </form>
      <p class='muted' style='margin-top:12px;'>Need an account? <a href='/ui/register?next={escape(next_path)}'>Register here</a></p>
    </div>
    """
    return render_page("Log In", "guest", guest_nav(), body)


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

    error_block = ""
    if error:
        error_block = f"<p style='color:#b91c1c; margin:0 0 12px 0;'>{escape(error)}</p>"

    body = f"""
    <div class='hero'>
      <h1>Register</h1>
      <p class='muted'>Create an account to access calendar management.</p>
    </div>
    <div class='card'>
      {error_block}
      <form method='POST' action='/ui/register?next={escape(next_path)}' style='display:flex; flex-direction:column; gap:10px; max-width:420px;'>
      <input type='text' name='name' placeholder='Name (optional)' style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='email' name='email' placeholder='Email' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='password' placeholder='Password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <input type='password' name='confirm_password' placeholder='Confirm password' required style='padding:10px; border:1px solid #cbd5e1; border-radius:10px;' />
      <button type='submit' class='btn' style='border:none; cursor:pointer; width:max-content; margin-top:0;'>Create Account</button>
      </form>
      <p class='muted' style='margin-top:12px;'>Already have an account? <a href='/ui/login?next={escape(next_path)}'>Log in</a></p>
    </div>
    """
    return render_page("Register", "guest", guest_nav(), body)


@ui_bp.route("/logout")
def logout():
    session.pop("ui_user", None)
    return redirect(url_for("ui.home"))
