import os
import json
import re
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
import gspread

app = Flask(__name__)

# Configure Cross-Origin Resource Sharing
CORS(app)

# Initialize Rate Limiter using client IP address
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day"],
    storage_uri="memory://"
)

# -------------------------------------------------------------------
# Configuration & Environment Variables
# -------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "portfolio_db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))


# -------------------------------------------------------------------
# Google Sheets Authentication Helper
# -------------------------------------------------------------------
def get_gspread_client():
    if "GOOGLE_CREDENTIALS" in os.environ:
        creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        return gspread.service_account_from_dict(creds_dict)
    if os.path.exists("credentials.json"):
        return gspread.service_account(filename="credentials.json")
    return None


# -------------------------------------------------------------------
# Storage Functions
# -------------------------------------------------------------------
def save_to_mysql(name, phone, email):
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        connect_timeout=5
    )
    cursor = conn.cursor()
    query = "INSERT INTO contacts (name, phone, email) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, phone, email))
    conn.commit()
    cursor.close()
    conn.close()


def save_to_sheets(name, phone, email):
    gc = get_gspread_client()
    if not gc:
        raise Exception("Google credentials not configured.")
    
    sheet = gc.open("Portfolio Contacts").sheet1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, name, phone, email])


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health():
    """Health check endpoint used for Render wake-up pings."""
    return jsonify({"status": "healthy"}), 200


@app.route("/api/contact", methods=["POST"])
@limiter.limit("5 per hour")  # Cap individual IP addresses to 5 submissions/hour
def contact():
    data = request.get_json() or {}

    # 1. Anti-Bot Honeypot: Reject silently if hidden field was populated
    if data.get("website_url"):
        # Return 201 so bots believe the submission succeeded
        return jsonify({"message": "Thank you! Your message has been sent."}), 201

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    # 2. Server-side Validation Layer
    if len(name) < 2 or len(name) > 80:
        return jsonify({"message": "Please enter a valid name (2-80 characters)."}), 400

    if not re.match(r"^\+?[0-9\s\-]{7,18}$", phone):
        return jsonify({"message": "Please enter a valid phone number."}), 400

    if len(email) > 254 or not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"message": "Please enter a valid email address."}), 400

    # 3. Dual Storage Operations with Fault Tolerance
    errors = []

    try:
        save_to_mysql(name, phone, email)
    except Exception as e:
        print(f"[ERROR] MySQL persistence failure: {e}")
        errors.append("mysql")

    try:
        save_to_sheets(name, phone, email)
    except Exception as e:
        print(f"[ERROR] Google Sheets persistence failure: {e}")
        errors.append("sheets")

    # If both persistent stores fail, notify client of internal service issue
    if len(errors) == 2:
        return jsonify({"message": "Service temporarily unavailable. Please try again later."}), 500

    return jsonify({"message": "Thank you! Your message has been sent."}), 201


# -------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "message": "Too many requests submitted from this IP. Please try again in an hour."
    }), 429


# -------------------------------------------------------------------
# Local Server Execution
# -------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)