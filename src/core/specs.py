"""
Spec management: CRUD for specs, tags, and developers.
PostgreSQL-backed.
"""

from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.extras

from src.config import settings

_initialized = False


@contextmanager
def _get_db():
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


def init_specs_db():
    global _initialized
    if _initialized:
        return
    with _get_db() as conn:
        cur = conn.cursor()
        # Role and display_name on users
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'pm'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT")
        # Developers
        cur.execute("""
            CREATE TABLE IF NOT EXISTS developers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                skills TEXT,
                notes TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # Specs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS specs (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'draft',
                priority TEXT DEFAULT 'medium',
                assigned_to INTEGER REFERENCES developers(id),
                created_by INTEGER REFERENCES users(id),
                chat_session_id TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # Tags
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#888'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS spec_tags (
                spec_id INTEGER REFERENCES specs(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (spec_id, tag_id)
            )
        """)
        # Conversations (chat history)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                session_id TEXT,
                title TEXT,
                context TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # Messages (for displaying chat history in UI)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
    _initialized = True


# --- Conversations ---

def list_conversations(user_id: int) -> list[dict]:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT * FROM conversations
            WHERE user_id = %s ORDER BY updated_at DESC
        """, (user_id,))
        return [dict(r) for r in cur.fetchall()]


def create_conversation(user_id: int, title: str = "Nuevo chat", session_id: str | None = None) -> dict:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            INSERT INTO conversations (user_id, title, session_id)
            VALUES (%s, %s, %s) RETURNING *
        """, (user_id, title, session_id))
        conn.commit()
        return dict(cur.fetchone())


def update_conversation(conv_id: int, **kwargs) -> dict | None:
    init_specs_db()
    allowed = {'title', 'session_id', 'context'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return None
    fields['updated_at'] = datetime.utcnow()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [conv_id]
        cur.execute(f"UPDATE conversations SET {set_clause} WHERE id = %s RETURNING *", values)
        conn.commit()
        row = cur.fetchone()
        return dict(row) if row else None


def delete_conversation(conv_id: int) -> bool:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM conversations WHERE id = %s", (conv_id,))
        conn.commit()
        return cur.rowcount > 0


def get_conversation_by_session(session_id: str) -> dict | None:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM conversations WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# --- Messages ---

def save_message(conversation_id: int, role: str, content: str):
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
            (conversation_id, role, content),
        )
        conn.commit()


def get_messages(conversation_id: int) -> list[dict]:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = %s ORDER BY created_at",
            (conversation_id,),
        )
        return [dict(r) for r in cur.fetchall()]


# --- Dynamic context for chat ---

def build_chat_context(conversation_context: str | None = None) -> str:
    """Build dynamic context string with current specs/devs state for Claude."""
    parts = []

    # Specs by status
    specs = list_specs()
    if specs:
        parts.append("## Estado actual del Kanban\n")
        by_status = {}
        for s in specs:
            by_status.setdefault(s['status'], []).append(s)
        status_labels = {'draft': 'Draft', 'ready': 'Ready', 'in_progress': 'In Progress', 'review': 'Review', 'done': 'Done'}
        for status, label in status_labels.items():
            items = by_status.get(status, [])
            if items:
                parts.append(f"**{label}:**")
                for s in items:
                    dev = f" (asignada a {s['dev_name']})" if s.get('dev_name') else ""
                    parts.append(f"- [id:{s['id']}] \"{s['title']}\" ({s['priority']}){dev}")
                parts.append("")

    # Developers
    devs = list_developers()
    if devs:
        parts.append("## Equipo de desarrollo\n")
        for d in devs:
            skills = f" — {d['skills']}" if d.get('skills') else ""
            parts.append(f"- [id:{d['id']}] {d['name']}{skills}")
        parts.append("")

    # Per-conversation context
    if conversation_context:
        parts.append(f"## Contexto de esta conversacion\n{conversation_context}\n")

    return "\n".join(parts)


# --- Specs ---

def list_specs(status: str | None = None, tag: str | None = None, assigned_to: int | None = None) -> list[dict]:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """
            SELECT s.*, d.name as dev_name,
                   array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags,
                   array_agg(DISTINCT t.color) FILTER (WHERE t.color IS NOT NULL) as tag_colors
            FROM specs s
            LEFT JOIN developers d ON s.assigned_to = d.id
            LEFT JOIN spec_tags st ON s.id = st.spec_id
            LEFT JOIN tags t ON st.tag_id = t.id
        """
        conditions = []
        params = []
        if status:
            conditions.append("s.status = %s")
            params.append(status)
        if assigned_to:
            conditions.append("s.assigned_to = %s")
            params.append(assigned_to)
        if tag:
            conditions.append("EXISTS (SELECT 1 FROM spec_tags st2 JOIN tags t2 ON st2.tag_id = t2.id WHERE st2.spec_id = s.id AND t2.name = %s)")
            params.append(tag)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " GROUP BY s.id, d.name ORDER BY s.updated_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def get_spec(spec_id: int) -> dict | None:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT s.*, d.name as dev_name,
                   array_agg(DISTINCT jsonb_build_object('id', t.id, 'name', t.name, 'color', t.color))
                       FILTER (WHERE t.id IS NOT NULL) as tags
            FROM specs s
            LEFT JOIN developers d ON s.assigned_to = d.id
            LEFT JOIN spec_tags st ON s.id = st.spec_id
            LEFT JOIN tags t ON st.tag_id = t.id
            WHERE s.id = %s
            GROUP BY s.id, d.name
        """, (spec_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_spec(title: str, content: str = "", priority: str = "medium",
                created_by: int | None = None, chat_session_id: str | None = None) -> dict:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            INSERT INTO specs (title, content, priority, created_by, chat_session_id)
            VALUES (%s, %s, %s, %s, %s) RETURNING *
        """, (title, content, priority, created_by, chat_session_id))
        conn.commit()
        return dict(cur.fetchone())


def update_spec(spec_id: int, **kwargs) -> dict | None:
    init_specs_db()
    allowed = {'title', 'content', 'status', 'priority', 'assigned_to', 'chat_session_id'}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return get_spec(spec_id)
    fields['updated_at'] = datetime.utcnow()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [spec_id]
        cur.execute(f"UPDATE specs SET {set_clause} WHERE id = %s RETURNING *", values)
        conn.commit()
        row = cur.fetchone()
        return dict(row) if row else None


def delete_spec(spec_id: int) -> bool:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM specs WHERE id = %s", (spec_id,))
        conn.commit()
        return cur.rowcount > 0


def set_spec_tags(spec_id: int, tag_ids: list[int]):
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM spec_tags WHERE spec_id = %s", (spec_id,))
        for tag_id in tag_ids:
            cur.execute("INSERT INTO spec_tags (spec_id, tag_id) VALUES (%s, %s)", (spec_id, tag_id))
        conn.commit()


# --- Tags ---

def list_tags() -> list[dict]:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM tags ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def create_tag(name: str, color: str = "#888") -> dict:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("INSERT INTO tags (name, color) VALUES (%s, %s) RETURNING *", (name, color))
        conn.commit()
        return dict(cur.fetchone())


# --- Developers ---

def list_developers() -> list[dict]:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM developers ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def get_developer(dev_id: int) -> dict | None:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM developers WHERE id = %s", (dev_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_developer(name: str, email: str = None, skills: str = None,
                     notes: str = None, created_by: int | None = None) -> dict:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            INSERT INTO developers (name, email, skills, notes, created_by)
            VALUES (%s, %s, %s, %s, %s) RETURNING *
        """, (name, email, skills, notes, created_by))
        conn.commit()
        return dict(cur.fetchone())


def update_developer(dev_id: int, **kwargs) -> dict | None:
    init_specs_db()
    allowed = {'name', 'email', 'skills', 'notes'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return get_developer(dev_id)
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [dev_id]
        cur.execute(f"UPDATE developers SET {set_clause} WHERE id = %s RETURNING *", values)
        conn.commit()
        row = cur.fetchone()
        return dict(row) if row else None


def delete_developer(dev_id: int) -> bool:
    init_specs_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE specs SET assigned_to = NULL WHERE assigned_to = %s", (dev_id,))
        cur.execute("DELETE FROM developers WHERE id = %s", (dev_id,))
        conn.commit()
        return cur.rowcount > 0
