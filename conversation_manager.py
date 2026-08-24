"""
Production Persistent SQLite Database Manager for NexusAI.
Includes User Account Management, Authentication, Sessions, Messages, and Memories.
"""

import os
import sqlite3
import json
import time
import uuid
import hashlib
from typing import Dict, List, Any, Optional

from config import DATA_DIR, MAX_CONVERSATION_TURNS, COMPANY_NAME, CEO_NAME

DB_PATH = os.path.join(DATA_DIR, "nexus_ai.db")

def hash_password(password: str) -> str:
    """Secure SHA-256 hash with salt for local password storage."""
    salt = "nexus_secure_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def init_db():
    """Initializes SQLite database schema with users, sessions, messages, and memories."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                auth_provider TEXT NOT NULL DEFAULT 'email',
                role TEXT NOT NULL DEFAULT 'user',
                occupation TEXT DEFAULT 'General User',
                created_at REAL NOT NULL,
                last_login REAL NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users(user_id)")

        # 2. Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at DESC)")

        # 3. Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                search_executed INTEGER NOT NULL DEFAULT 0,
                sources_json TEXT NOT NULL DEFAULT '[]',
                timestamp REAL NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id ASC)")

        # 4. Memories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                updated_at REAL NOT NULL,
                UNIQUE(user_id, key)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
        conn.commit()

init_db()


class PersistentConversationManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        init_db()

    # User Authentication & Management Methods
    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        occupation: str = "General User",
        auth_provider: str = "email"
    ) -> Dict[str, Any]:
        clean_email = email.lower().strip()
        clean_name = name.strip() or "Nexus User"
        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        now = time.time()

        # Check if email is Founder / CEO
        is_founder = "hammad" in clean_email or "hammad" in clean_name.lower()
        role = "ceo" if is_founder else "user"

        pw_hash = hash_password(password) if password else "oauth_managed"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (user_id, email, name, password_hash, auth_provider, role, occupation, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, clean_email, clean_name, pw_hash, auth_provider, role, occupation.strip() or "General User", now, now)
            )
            conn.commit()

        return {
            "user_id": user_id,
            "email": clean_email,
            "name": clean_name,
            "role": role,
            "occupation": occupation,
            "auth_provider": auth_provider,
            "created_at": now
        }

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        clean_email = email.lower().strip()
        pw_hash = hash_password(password)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, email, name, role, occupation, auth_provider, created_at
                FROM users
                WHERE email = ? AND password_hash = ?
                """,
                (clean_email, pw_hash)
            )
            row = cursor.fetchone()
            if row:
                now = time.time()
                cursor.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (now, row[0]))
                conn.commit()
                return {
                    "user_id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "role": row[3],
                    "occupation": row[4],
                    "auth_provider": row[5],
                    "created_at": row[6]
                }
        return None

    def get_or_create_google_user(self, email: str, name: str, picture: Optional[str] = None) -> Dict[str, Any]:
        """Handles 1-Click Google Sign-In, creating account if new or logging in if exists."""
        clean_email = email.lower().strip()
        clean_name = name.strip() or "Google User"
        now = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, email, name, role, occupation, auth_provider, created_at FROM users WHERE email = ?", (clean_email,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE users SET last_login = ? WHERE user_id = ?", (now, row[0]))
                conn.commit()
                return {
                    "user_id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "role": row[3],
                    "occupation": row[4],
                    "auth_provider": row[5],
                    "created_at": row[6]
                }
            else:
                user_id = f"usr_{uuid.uuid4().hex[:10]}"
                is_founder = "hammad" in clean_email or "hammad" in clean_name.lower()
                role = "ceo" if is_founder else "user"
                cursor.execute(
                    """
                    INSERT INTO users (user_id, email, name, password_hash, auth_provider, role, occupation, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, clean_email, clean_name, "google_oauth_verified", "google", role, "Google User", now, now)
                )
                conn.commit()
                return {
                    "user_id": user_id,
                    "email": clean_email,
                    "name": clean_name,
                    "role": role,
                    "occupation": "Google User",
                    "auth_provider": "google",
                    "created_at": now
                }

    def list_all_users_for_admin(self) -> List[Dict[str, Any]]:
        """CEO-only: List all registered user records stored in local SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.user_id, u.email, u.name, u.role, u.occupation, u.auth_provider, u.created_at, u.last_login,
                       COUNT(DISTINCT s.session_id) as total_chats
                FROM users u
                LEFT JOIN sessions s ON u.user_id = s.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "user_id": r[0],
                    "email": r[1],
                    "name": r[2],
                    "role": r[3],
                    "occupation": r[4],
                    "auth_provider": r[5],
                    "created_at": r[6],
                    "last_login": r[7],
                    "total_chats": r[8]
                }
                for r in rows
            ]

    # Session & Chat Methods
    def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        safe_uid = user_id or "default_user"
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("SELECT session_id, user_id, title, created_at, updated_at FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, safe_uid))
                row = cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "created_at": row[3],
                        "updated_at": row[4]
                    }

            new_id = session_id if session_id else str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (new_id, safe_uid, "New Conversation", now, now)
            )
            conn.commit()
            return {
                "session_id": new_id,
                "user_id": safe_uid,
                "title": "New Conversation",
                "created_at": now,
                "updated_at": now
            }

    def add_user_turn(self, user_id: str, session_id: str, content: str):
        safe_uid = user_id or "default_user"
        now = time.time()
        session = self.get_or_create_session(safe_uid, session_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if session["title"] == "New Conversation":
                clean_title = content.strip().split("\n")[0][:45] or "Conversation"
                cursor.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?", (clean_title, now, session_id))
            else:
                cursor.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))

            cursor.execute(
                "INSERT INTO messages (session_id, user_id, role, content, search_executed, sources_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, safe_uid, "user", content, 0, "[]", now)
            )
            conn.commit()

    def add_assistant_turn(self, user_id: str, session_id: str, content: str, search_executed: bool = False, sources: Optional[List[Dict[str, Any]]] = None):
        safe_uid = user_id or "default_user"
        now = time.time()
        sources_json = json.dumps(sources or [])
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            cursor.execute(
                "INSERT INTO messages (session_id, user_id, role, content, search_executed, sources_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, safe_uid, "assistant", content, 1 if search_executed else 0, sources_json, now)
            )
            conn.commit()

    def get_llm_messages(self, user_id: str, session_id: str, max_turns: int = 12) -> List[Dict[str, str]]:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages WHERE session_id = ? AND user_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, safe_uid, max_turns)
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.session_id, s.title, s.updated_at, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                WHERE s.user_id = ?
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
                LIMIT 50
            """, (safe_uid,))
            rows = cursor.fetchall()
            return [
                {
                    "session_id": r[0],
                    "title": r[1],
                    "updated_at": r[2],
                    "message_count": r[3]
                }
                for r in rows
            ]

    def get_session_history(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, user_id, title, created_at, updated_at FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, safe_uid))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "SELECT role, content, search_executed, sources_json, timestamp FROM messages WHERE session_id = ? AND user_id = ? ORDER BY id ASC",
                (session_id, safe_uid)
            )
            msg_rows = cursor.fetchall()
            messages = []
            for mr in msg_rows:
                try:
                    srcs = json.loads(mr[3])
                except Exception:
                    srcs = []
                messages.append({
                    "role": mr[0],
                    "content": mr[1],
                    "search_executed": bool(mr[2]),
                    "sources": srcs,
                    "timestamp": mr[4]
                })

            return {
                "session_id": row[0],
                "user_id": row[1],
                "title": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "messages": messages
            }

    def delete_session(self, user_id: str, session_id: str) -> bool:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ? AND user_id = ?", (session_id, safe_uid))
            cursor.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, safe_uid))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self, user_id: str):
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE user_id = ?", (safe_uid,))
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (safe_uid,))
            conn.commit()
