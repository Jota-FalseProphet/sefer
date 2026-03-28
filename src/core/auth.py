"""
User authentication: register/login with email+password.
PostgreSQL-backed, passwords hashed with PBKDF2, email verification required.
"""

import hashlib
import hmac
import os
import random
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from src.config import settings

VERIFICATION_CODE_EXPIRY_MINUTES = 10

_initialized = False


@contextmanager
def _get_db():
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    global _initialized
    if _initialized:
        return
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                verified BOOLEAN DEFAULT FALSE,
                claude_authenticated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS verification_codes (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
    _initialized = True


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
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email.lower().strip(), _hash_password(password)),
            )
            conn.commit()
            return {"ok": True}
        except psycopg2.IntegrityError:
            conn.rollback()
            return {"ok": False, "error": "Email already registered"}


def login(email: str, password: str) -> dict:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email.lower().strip(),))
        row = cur.fetchone()
        if not row or not _verify_password(password, row["password_hash"]):
            return {"ok": False, "error": "Invalid email or password"}
        if not row["verified"]:
            return {"ok": False, "error": "Email not verified. Check your inbox."}
        token = secrets.token_urlsafe(48)
        cur.execute(
            "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
            (token, row["id"]),
        )
        conn.commit()
        return {"ok": True, "token": token, "user_id": row["id"], "email": row["email"]}


def get_user_by_token(token: str) -> dict | None:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT u.id, u.email, u.claude_authenticated
            FROM sessions s JOIN users u ON s.user_id = u.id
            WHERE s.token = %s
        """, (token,))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row["id"], "email": row["email"], "claude_authenticated": bool(row["claude_authenticated"])}


def set_claude_authenticated(user_id: int, value: bool = True):
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET claude_authenticated = %s WHERE id = %s", (value, user_id))
        conn.commit()


def create_verification_code(email: str) -> str:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        # Invalidate previous codes
        cur.execute(
            "UPDATE verification_codes SET used = TRUE WHERE email = %s AND used = FALSE",
            (email.lower().strip(),),
        )
        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)
        cur.execute(
            "INSERT INTO verification_codes (email, code, expires_at) VALUES (%s, %s, %s)",
            (email.lower().strip(), code, expires_at),
        )
        conn.commit()
        return code


def verify_code(email: str, code: str) -> dict:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT * FROM verification_codes
            WHERE email = %s AND code = %s AND used = FALSE
            ORDER BY created_at DESC LIMIT 1
        """, (email.lower().strip(), code))
        row = cur.fetchone()

        if not row:
            return {"ok": False, "error": "Invalid verification code"}

        if row["expires_at"].replace(tzinfo=None) < datetime.utcnow():
            return {"ok": False, "error": "Code expired. Request a new one."}

        # Mark code as used and user as verified
        cur.execute("UPDATE verification_codes SET used = TRUE WHERE id = %s", (row["id"],))
        cur.execute("UPDATE users SET verified = TRUE WHERE email = %s", (email.lower().strip(),))
        conn.commit()
        return {"ok": True}
