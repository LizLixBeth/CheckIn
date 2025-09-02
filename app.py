from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3, os, datetime

APP_NAME = os.getenv("APP_NAME", "Daily Check-In")
DB_PATH = os.getenv("DATABASE_URL", "checkins.db")  # sqlite file path

app = Flask(__name__)

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                energy_level TEXT NOT NULL,
                symptom_level TEXT NOT NULL,
                overall_vibes TEXT NOT NULL,
                support_needed INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'On time'
            )'''
        )
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                checkin_id INTEGER,
                type TEXT NOT NULL,
                follow_up TEXT NOT NULL DEFAULT 'None',
                status TEXT NOT NULL DEFAULT 'Unread',
                FOREIGN KEY(checkin_id) REFERENCES checkins(id) ON DELETE SET NULL
            )'''
        )
        con.commit()

# Initialize DB once at startup (Flask 3+ friendly)
init_db()


def create_message_rows(now_iso, checkin_id, status, support_needed):
    msgs = []
    if status in ("Late", "Missed", "Extra"):
        follow = "Low" if status == "Late" else "None"
        msgs.append((now_iso, checkin_id, "Notices", follow, "Unread"))
    if support_needed:
        msgs.append((now_iso, checkin_id, "Support Requested", "High", "Unread"))
    return msgs

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", app_name=APP_NAME)

@app.route("/dashboard", methods=["GET"])
def dashboard():
    # Fetch recent entries
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM checkins ORDER BY created_at DESC LIMIT 100")
        checkins = cur.fetchall()
        cur.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 100")
        messages = cur.fetchall()
    return render_template("dashboard.html", app_name=APP_NAME, checkins=checkins, messages=messages)

@app.route("/submit", methods=["POST"])
def submit():
    # Accept standard form POST or JSON
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
    else:
        data = request.form.to_dict()

    now_iso = datetime.datetime.utcnow().isoformat()
    energy_level = data.get("energy_level", "")
    symptom_level = data.get("symptom_level", "")
    overall_vibes = data.get("overall_vibes", "")
    support_needed = 1 if str(data.get("support_needed", "")).lower() in ("1","true","on","yes") else 0
    status = data.get("status", "On time")

    if not (energy_level and symptom_level and overall_vibes):
        msg = "Missing required fields."
        if request.is_json:
            return jsonify({"ok": False, "error": msg}), 400
        return msg, 400

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO checkins (created_at, energy_level, symptom_level, overall_vibes, support_needed, status) VALUES (?, ?, ?, ?, ?, ?)",
            (now_iso, energy_level, symptom_level, overall_vibes, support_needed, status)
        )
        checkin_id = cur.lastrowid
        # Create messages
        msgs = create_message_rows(now_iso, checkin_id, status, bool(support_needed))
        if msgs:
            cur.executemany(
                "INSERT INTO messages (created_at, checkin_id, type, follow_up, status) VALUES (?, ?, ?, ?, ?)",
                msgs
            )
        con.commit()

    # redirect if form-post, else json
    if request.is_json:
        return jsonify({"ok": True, "id": checkin_id})
    else:
        return redirect(url_for("dashboard"))

@app.route("/api/checkins", methods=["GET"])
def api_checkins():
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM checkins ORDER BY created_at DESC LIMIT 100")
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route("/api/messages", methods=["GET"])
def api_messages():
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 100")
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)