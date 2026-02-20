import os
import json
from supabase import create_client

# Initialize Supabase client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

def handler(request):
    # Vercel's runtime passes a dictionary-like request object
    if request["httpMethod"] == "POST":
        try:
            data = request.get("body")
            if data:
                data = json.loads(data)
                name = data.get("name")
                email = data.get("email")

                if not name or not email:
                    return {
                        "statusCode": 400,
                        "body": '{"error": "Name and email are required"}'
                    }

                # Insert into Supabase
                response = supabase.table("users").insert({"name": name, "email": email}).execute()

                if response.status_code == 201:
                    return {
                        "statusCode": 201,
                        "body": '{"message": "User created successfully"}'
                    }
                else:
                    return {
                        "statusCode": 500,
                        "body": '{"error": "Failed to create user"}'
                    }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": f'{{"error": "{str(e)}"}}'
            }

    return {
        "statusCode": 200,
        "body": '{"message": "Welcome to the API!"}'
    }