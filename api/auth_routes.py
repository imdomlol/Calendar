from flask import Blueprint, request
from supabase_client import get_supabase_client

auth_bp = Blueprint("auth", __name__)
supabase = get_supabase_client()

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        if not email or not password:
            return {"error": "Email and password required"}, 400

        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if result.user:
            supabase.table("users").insert({
                "id": result.user.id,
                "name": name,
                "email": email
            }).execute()

        return {
            "message": "User created",
            "session": result.session,
            "user": result.user
        }, 201

    except Exception as e:
        return {"error": str(e)}, 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email and password required"}, 400

        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        return {
            "message": "Login successful",
            "session": result.session,
            "user": result.user
        }, 200

    except Exception:
        return {"error": "Invalid credentials"}, 401