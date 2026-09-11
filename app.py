from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import re
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
CORS(app)

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zuhu1902',  # Your MySQL root password
    'database': 'portfolio_db'
}

# Google Sheets Configuration
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def append_to_google_sheet(name, phone, email):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
        client = gspread.authorize(creds)
        
        # Open by title
        sheet = client.open("Portfolio Contacts").sheet1
        
        # Current readable timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Append as a new row: [Timestamp, Name, Phone, Email]
        sheet.append_row([timestamp, name, phone, email])
    except Exception as e:
        # Print error to terminal without blocking the response to the user
        print(f"Failed to append to Google Sheets: {e}")

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
PHONE_REGEX = r'^\+?[0-9\s\-]{7,15}$'

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received."}), 400

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    # Validation
    if len(name) < 2:
        return jsonify({"status": "error", "message": "Please enter a valid name."}), 400
    if not re.match(PHONE_REGEX, phone):
        return jsonify({"status": "error", "message": "Please enter a valid phone number."}), 400
    if not re.match(EMAIL_REGEX, email):
        return jsonify({"status": "error", "message": "Please enter a valid email address."}), 400

    # 1. Insert into MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "INSERT INTO contacts (name, phone, email) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, phone, email))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500

    # 2. Append to Google Sheets
    append_to_google_sheet(name, phone, email)

    return jsonify({"status": "success", "message": "Thank you! Your message has been sent."}), 201

if __name__ == '__main__':
    print("Server running on http://127.0.0.1:5000")
    app.run(port=5000, debug=True)