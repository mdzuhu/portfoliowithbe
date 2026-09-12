import os
import json
import re
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import gspread

app = Flask(__name__)
CORS(app)

# MySQL Connection Configurations
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "portfolio_db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_gspread_client():
    """Authenticates gspread using Render Environment Variable or local file."""
    if "GOOGLE_CREDENTIALS" in os.environ:
        creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        return gspread.service_account_from_dict(creds_dict)
    if os.path.exists("credentials.json"):
        return gspread.service_account(filename="credentials.json")
    return None

def save_to_mysql(name, phone, email):
    """Inserts contact record into MySQL database."""
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
    """Appends submission row with timestamp to Google Sheets."""
    gc = get_gspread_client()
    if not gc:
        raise Exception("Google credentials not configured.")
    
    sheet = gc.open("Portfolio Contacts").sheet1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, name, phone, email])

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    # Validations
    if len(name) < 2:
        return jsonify({"message": "Please enter a valid name."}), 400
    if not re.match(r"^\+?[0-9\s\-]{7,15}$", phone):
        return jsonify({"message": "Please enter a valid phone number."}), 400
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return jsonify({"message": "Please enter a valid email address."}), 400

    errors = []

    # 1. MySQL Entry
    try:
        save_to_mysql(name, phone, email)
    except Exception as e:
        print(f"MySQL error: {e}")
        errors.append("mysql")

    # 2. Simultaneous Google Sheets Entry
    try:
        save_to_sheets(name, phone, email)
    except Exception as e:
        print(f"Google Sheets error: {e}")
        errors.append("sheets")

    # If both failed completely, notify the user
    if len(errors) == 2:
        return jsonify({"message": "Database services temporarily unavailable."}), 500

    return jsonify({"message": "Thank you! Your message has been sent."}), 201

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)