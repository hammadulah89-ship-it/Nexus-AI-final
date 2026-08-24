"""
Pillar 8: Persistent SQLite Multi-User Memory Vault & Core Leadership Knowledge.
"""

import os
import sqlite3
import time
from typing import Dict, List, Any, Optional
from config import DATA_DIR, COMPANY_NAME, CEO_NAME

DB_PATH = os.path.join(DATA_DIR, "nexus_ai.db")

class MemoryVault:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def remember(self, user_id: str, key: str, value: str, category: str = "general") -> Dict[str, Any]:
        safe_uid = user_id or "default_user"
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (user_id, key, value, category, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value=excluded.value,
                    category=excluded.category,
                    updated_at=excluded.updated_at
            """, (safe_uid, key.strip(), value.strip(), category.strip(), now))
            conn.commit()
            return {
                "key": key.strip(),
                "value": value.strip(),
                "category": category.strip(),
                "updated_at": now
            }

    def recall(self, user_id: str, query: str = "") -> List[Dict[str, Any]]:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not query:
                cursor.execute("SELECT key, value, category, updated_at FROM memories WHERE user_id = ? ORDER BY updated_at DESC", (safe_uid,))
            else:
                like_pattern = f"%{query.lower()}%"
                cursor.execute("SELECT key, value, category, updated_at FROM memories WHERE user_id = ? AND (LOWER(key) LIKE ? OR LOWER(value) LIKE ?) ORDER BY updated_at DESC", (safe_uid, like_pattern, like_pattern))
            
            rows = cursor.fetchall()
            return [
                {
                    "key": r[0],
                    "value": r[1],
                    "category": r[2],
                    "updated_at": r[3]
                }
                for r in rows
            ]

    def forget(self, user_id: str, key: str) -> bool:
        safe_uid = user_id or "default_user"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE user_id = ? AND key = ?", (safe_uid, key.strip()))
            conn.commit()
            return cursor.rowcount > 0

    def get_context_prompt(self, user_id: str, is_ceo_authenticated: bool = False, caller_name: Optional[str] = None) -> str:
        safe_uid = user_id or "default_user"
        memories = self.recall(safe_uid)
        
        lines = [
            "[IMMUTABLE CORPORATE IDENTITY & LEADERSHIP KNOWLEDGE]",
            f"• Creator & Organization: {COMPANY_NAME}",
            f"• Founder & CEO / Owner: {CEO_NAME}",
            "• System Identity: NexusAI Autonomous AI Operating System (Version 4.5)",
            f"• Verified CEO / Boss Status: {'AUTHENTICATED CEO (Mr. Hammadullah Khalid) - Full VIP Executive Access' if is_ceo_authenticated else 'Standard User / Visitor (Not authenticated as CEO)'}",
            "[END CORPORATE KNOWLEDGE]\n"
        ]

        if memories:
            lines.append("[PRIVATE USER MEMORY & PROFILE]")
            for item in memories:
                lines.append(f"- {item['key']}: {item['value']}")
            lines.append("[END USER MEMORY]\n")

        return "\n".join(lines)
