"""
User authentication: register/login with email+password.
SQLite-backed, passwords hashed with bcrypt.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sefer.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            claude_authenticated INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(key.hex(), key_hex)


def register(email: str, password: str) -> dict:
    db = _get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.lower().strip(), _hash_password(password)),
        )
        db.commit()
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Email already registered"}
    finally:
        db.close()


def login(email: str, password: str) -> dict:
    db = _get_db()
    try:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
        if not row or not _verify_password(password, row["password_hash"]):
            return {"ok": False, "error": "Invalid email or password"}
        token = secrets.token_urlsafe(48)
        db.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, row["id"]),
        )
        db.commit()
        return {"ok": True, "token": token, "user_id": row["id"], "email": row["email"]}
    finally:
        db.close()


def get_user_by_token(token: str) -> dict | None:
    db = _get_db()
    try:
        row = db.execute("""
            SELECT u.id, u.email, u.claude_authenticated
            FROM sessions s JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,)).fetchone()
        if not row:
            return None
        return {"id": row["id"], "email": row["email"], "claude_authenticated": bool(row["claude_authenticated"])}
    finally:
        db.close()


def set_claude_authenticated(user_id: int, value: bool = True):
    db = _get_db()
    try:
        db.execute("UPDATE users SET claude_authenticated = ? WHERE id = ?", (int(value), user_id))
        db.commit()
    finally:
        db.close()
