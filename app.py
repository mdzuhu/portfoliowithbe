import os
import json
import re
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread

app = Flask(__name__)
# Enable CORS for your Vercel frontend and local testing
CORS(app)

# Database credentials
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'YOUR_ACTUAL_ROOT_PASSWORD')  # Replace with your local MySQL password
DB_NAME = os.environ.get('DB_NAME', 'portfolio_db')

def get_gspread_client():
    """
    Authenticate with Google Sheets.
    Uses environment variable on Render, falls back to local credentials.json.
    """
    if "GOOGLE_CREDENTIALS" in os.environ:
        creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        return gspread.service_account_from_dict(creds_dict)
    return gspread.service_account(filename="credentials.json")

def append_to_google_sheet(name, phone, email):
    """Logs the submitted contact details to Google Sheets."""
    try:
        gc = get_gspread_client()
        sheet = gc.open("Portfolio Contacts").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, name, phone, email])
        print("Logged submission to Google Sheets successfully.")
    except Exception as e:
        print(f"Warning: Failed to log to Google Sheets: {e}")

def save_to_mysql(name, phone, email):
    """Logs to MySQL when available, catches error gracefully if offline."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=3
        )
        cursor = conn.cursor()
        sql = "INSERT INTO contacts (name, phone, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, phone, email))
        conn.commit()
        cursor.close()
        conn.close()
        print("Logged to MySQL successfully.")
    except Exception as e:
        print(f"MySQL note: {e}")

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
PHONE_REGEX = r'^\+?[0-9\s\-]{7,15}$'

@app.route('/', methods=['GET'])
def health_check():
    """Root route so Render's health checks pass instantly."""
    return jsonify({"status": "healthy", "service": "portfolio-backend"}), 200

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received."}), 400

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    # Form Validations
    if len(name) < 2:
        return jsonify({"status": "error", "message": "Please enter a valid name."}), 400
    if not re.match(PHONE_REGEX, phone):
        return jsonify({"status": "error", "message": "Please enter a valid phone number."}), 400
    if not re.match(EMAIL_REGEX, email):
        return jsonify({"status": "error", "message": "Please enter a valid email address."}), 400

    # Save to databases
    save_to_mysql(name, phone, email)
    append_to_google_sheet(name, phone, email)

    return jsonify({"status": "success", "message": "Thank you! Your message has been sent."}), 201

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)