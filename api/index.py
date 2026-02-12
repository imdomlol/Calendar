import os
from supabase import create_client

supabase = create_client(
    os.environ["SUPABASE_URL"], 
    os.environ["SUPABASE_KEY"],
)

def handler(request):
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            return {"error": "Name and email are required"}, 400

        # Insert the new user into the database
        response = supabase.table("users").insert({"name": name, "email": email}).execute()

        if response.status_code == 201:
            return {"message": "User created successfully"}, 201
        else:
            return {"error": "Failed to create user"}, 500

    return {"message": "Welcome to the API!"}, 200