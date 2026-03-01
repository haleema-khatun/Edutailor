import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Skills table (legacy)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        python INTEGER,
        ml INTEGER,
        dsa INTEGER,
        dbms INTEGER
    )
    """)

    # User progress tracking
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        score INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

def create_user(username, email, password):
    """Create a new user. Returns (True, msg) or (False, error_msg)."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already exists."
        elif "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."
    finally:
        conn.close()

def get_user(username):
    """Get user by username. Returns dict or None."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def verify_user(username, password):
    """Verify login credentials. Returns (True, user_dict) or (False, error_msg)."""
    user = get_user(username)
    if not user:
        return False, "User not found."
    if not check_password_hash(user["password_hash"], password):
        return False, "Incorrect password."
    return True, user

def save_progress(user_id, category, subject, score):
    """Save a progress entry."""
    conn = get_db()
    conn.execute(
        "INSERT INTO user_progress (user_id, category, subject, score) VALUES (?, ?, ?, ?)",
        (user_id, category, subject, score)
    )
    conn.commit()
    conn.close()

def get_progress(user_id):
    """Get all progress for a user, grouped by category."""
    conn = get_db()
    rows = conn.execute(
        "SELECT category, subject, score, timestamp FROM user_progress WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    progress = {"learning": [], "interview": [], "resume": []}
    for row in rows:
        r = dict(row)
        cat = r["category"]
        if cat in progress:
            progress[cat].append(r)

    return progress

def get_progress_summary(user_id):
    """Get summary stats for analytics."""
    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) as total FROM user_progress WHERE user_id = ?", (user_id,)
    ).fetchone()

    avg = conn.execute(
        "SELECT AVG(score) as avg_score FROM user_progress WHERE user_id = ?", (user_id,)
    ).fetchone()

    best = conn.execute(
        "SELECT subject, MAX(score) as max_score FROM user_progress WHERE user_id = ? GROUP BY subject ORDER BY max_score DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    # Per-category average
    cat_avg = conn.execute(
        "SELECT category, AVG(score) as avg_score FROM user_progress WHERE user_id = ? GROUP BY category",
        (user_id,)
    ).fetchall()

    # Recent scores (last 10)
    recent = conn.execute(
        "SELECT subject, score, timestamp FROM user_progress WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # Per-subject latest score
    subject_scores = conn.execute(
        """SELECT subject, score FROM user_progress WHERE user_id = ? 
           AND id IN (SELECT MAX(id) FROM user_progress WHERE user_id = ? GROUP BY subject)""",
        (user_id, user_id)
    ).fetchall()

    conn.close()

    return {
        "total_assessments": total["total"] if total else 0,
        "avg_score": round(avg["avg_score"], 1) if avg and avg["avg_score"] else 0,
        "best_subject": dict(best) if best else None,
        "category_averages": {dict(r)["category"]: round(dict(r)["avg_score"], 1) for r in cat_avg},
        "recent": [dict(r) for r in recent],
        "subject_scores": {dict(r)["subject"]: dict(r)["score"] for r in subject_scores}
    }
