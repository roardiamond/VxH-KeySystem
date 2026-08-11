from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import secrets
import string
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-to-a-random-secret-key-please")
CORS(app)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DB_PATH = "keys.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_code TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            note TEXT,
            is_active INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def generate_key():
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return f"VxH-{'-'.join(parts)}"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "VxH Key System",
        "endpoints": {
            "validate": "POST /api/validate",
            "admin": "/admin"
        }
    })

@app.route("/api/validate", methods=["POST"])
def validate_key():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip().upper()

    if not key:
        return jsonify({"valid": False, "message": "Key is required"}), 400

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM keys WHERE key_code = ? AND is_active = 1",
        (key,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"valid": False, "message": "Invalid or revoked key"})

    expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()

    if now > expires_at:
        conn.close()
        return jsonify({
            "valid": False,
            "message": "Key has expired",
            "expires_at": row["expires_at"]
        })

    # Increase used count
    conn.execute(
        "UPDATE keys SET used_count = used_count + 1 WHERE id = ?",
        (row["id"],)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "valid": True,
        "message": "Key is valid",
        "expires_at": row["expires_at"],
        "note": row["note"] or ""
    })

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin_panel"))
        return render_template("login.html", error="Wrong password")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@login_required
def admin_panel():
    conn = get_db()
    keys = conn.execute(
        "SELECT * FROM keys ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("admin.html", keys=keys)

@app.route("/admin/generate", methods=["POST"])
@login_required
def generate():
    expires_at = request.form.get("expires_at", "").strip()
    note = request.form.get("note", "").strip()

    if not expires_at:
        return redirect(url_for("admin_panel"))

    # Convert HTML datetime-local to our format
    try:
        dt = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M")
        expires_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        expires_str = expires_at

    key_code = generate_key()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO keys (key_code, created_at, expires_at, note) VALUES (?, ?, ?, ?)",
            (key_code, created_at, expires_str, note)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    return redirect(url_for("admin_panel"))

@app.route("/admin/revoke/<int:key_id>", methods=["POST"])
@login_required
def revoke(key_id):
    conn = get_db()
    conn.execute("UPDATE keys SET is_active = 0 WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete/<int:key_id>", methods=["POST"])
@login_required
def delete_key(key_id):
    conn = get_db()
    conn.execute("DELETE FROM keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))

# -------- IMPORTANT FIX --------
# Call init_db() at module level so it runs with gunicorn / Render
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
