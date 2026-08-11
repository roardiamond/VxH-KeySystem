from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
import os
from functools import wraps
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "VxH_Secret_Key_Change_Me_2026")
CORS(app)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
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
        print("[VxH] Database initialized successfully")
    except Exception as e:
        print(f"[VxH] DB init error: {e}")

def generate_key_code():
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
            "generate": "POST /api/generate  (needs admin password)",
            "admin": "/admin"
        }
    })

@app.route("/api/validate", methods=["POST"])
def validate_key():
    try:
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

        try:
            expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
        except:
            expires_at = datetime.strptime(row["expires_at"][:19], "%Y-%m-%d %H:%M:%S")

        now = datetime.now()

        if now > expires_at:
            conn.close()
            return jsonify({
                "valid": False,
                "message": "Key has expired",
                "expires_at": row["expires_at"]
            })

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
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"valid": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Generate key via API (more reliable than admin panel)"""
    try:
        data = request.get_json(silent=True) or {}
        password = data.get("password", "")
        days = int(data.get("days", 30))
        hours = int(data.get("hours", 0))
        note = data.get("note", "")

        if password != ADMIN_PASSWORD:
            return jsonify({"success": False, "message": "Wrong admin password"}), 403

        if days < 0 or hours < 0:
            return jsonify({"success": False, "message": "Invalid time"}), 400

        expires_at = datetime.now() + timedelta(days=days, hours=hours)
        expires_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        key_code = generate_key_code()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO keys (key_code, created_at, expires_at, note) VALUES (?, ?, ?, ?)",
            (key_code, created_at, expires_str, note)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "key": key_code,
            "expires_at": expires_str,
            "message": "Key generated successfully"
        })
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    try:
        if request.method == "POST":
            password = request.form.get("password", "")
            if password == ADMIN_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("admin_panel"))
            return render_template("login.html", error="Wrong password")
        return render_template("login.html")
    except Exception as e:
        return f"Login Error: {str(e)}", 500

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin")
@login_required
def admin_panel():
    try:
        conn = get_db()
        keys = conn.execute("SELECT * FROM keys ORDER BY id DESC").fetchall()
        conn.close()
        return render_template("admin.html", keys=keys)
    except Exception as e:
        print(traceback.format_exc())
        return f"Admin Panel Error: {str(e)}<br><pre>{traceback.format_exc()}</pre>", 500

@app.route("/admin/generate", methods=["POST"])
@login_required
def generate():
    try:
        expires_at = request.form.get("expires_at", "").strip()
        note = request.form.get("note", "").strip()

        if not expires_at:
            return redirect(url_for("admin_panel"))

        try:
            dt = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M")
            expires_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            expires_str = expires_at

        key_code = generate_key_code()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO keys (key_code, created_at, expires_at, note) VALUES (?, ?, ?, ?)",
            (key_code, created_at, expires_str, note)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_panel"))
    except Exception as e:
        print(traceback.format_exc())
        return f"Generate Error: {str(e)}", 500

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

# Initialize DB when app starts
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
