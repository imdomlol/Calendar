from http.server import BaseHTTPRequestHandler
import json
import os
from supabase import create_client
from flask import Flask, g, request
from flask_cors import CORS
from utils.auth import require_auth

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

app = Flask(__name__)

@app.route("/")
def welcome():
    return {"message": "Welcome to the API!"}

# Configure CORS to allow frontend
CORS(app, resources={r"/api/*": {"origins": "https://your-domain.com"}})

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    logger.error(f"Bad request: {str(e)}")
    return {"error": str(e)}, 400

@app.errorhandler(401)
def unauthorized(e):
    logger.error(f"Unauthorized: {str(e)}")
    return {"error": "Unauthorized"}, 401

@app.errorhandler(404)
def not_found(e):
    logger.error(f"Not found: {str(e)}")
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return {"error": "Internal server error"}, 500

@app.route("/")
def index():
    return {"message": "Welcome to the API!"}


@app.route("/me", methods=["GET"])
@require_auth
def me():
    user = getattr(g, "user", {})
    return {
        "success": True,
        "user": {
            "id": user.get("id") or user.get("sub"),
            "email": user.get("email"),
            "role": user.get("role"),
            "last_sign_in_at": user.get("last_sign_in_at"),
        },
        "session": {
            "authenticated": True,
        },
    }, 200

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"message": "Welcome to the API!"}')

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            name = data.get("name")
            email = data.get("email")

            if not name or not email:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Name and email are required"}')
                return

            response = supabase.table("users").insert({"name": name, "email": email}).execute()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message": "User created successfully"}')

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())