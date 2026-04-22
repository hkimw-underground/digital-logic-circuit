from flask import Flask, render_template, jsonify, request
from config import FLASK_DEBUG, LEGACY_FLASK_PORT, WEB_HOST
from database import Database
from validation import RegistrationValidationError, validate_registration

app = Flask(__name__)
db = None


def get_db():
    global db
    if db is None:
        db = Database()
    return db

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/api/logs')
def get_logs():
    database = get_db()
    logs = [
        {
            "timestamp": row["timestamp"],
            "user": row["username"],
            "method": row["method"],
            "status": row["status"],
        }
        for row in database.get_recent_logs(limit=20)
    ]
    return jsonify({"logs": logs, "alert": database.has_consecutive_failures(limit=3)})

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json(silent=True) or {}
    try:
        name, nfc_uid, password = validate_registration(
            data.get('name'),
            data.get('nfc_uid'),
            data.get('password'),
        )
    except RegistrationValidationError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    
    user_id = get_db().add_user(name, nfc_uid=nfc_uid, password=password)
    if user_id:
        return jsonify({"success": True, "message": "User registered successfully!"})
    return jsonify({"success": False, "message": "NFC UID already exists!"}), 409

if __name__ == "__main__":
    app.run(host=WEB_HOST, port=LEGACY_FLASK_PORT, debug=FLASK_DEBUG)
