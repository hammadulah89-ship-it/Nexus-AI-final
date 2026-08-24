"""
Configuration manager for NexusAI Autonomous Agentic OS.
Dynamic portable path detection with Zero-Trust Secret Isolation.
"""

import os
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_env():
    """Loads environment variables from local .env file if present."""
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env()

# Core Neural API Keys (Loaded strictly from environment / .env, never hardcoded in source)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# Google OAuth 2.0 Credentials (Loaded from environment / .env)
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Executive Leadership & Corporate Identity
COMPANY_NAME: str = "Nexus Technologies Limited"
CEO_NAME: str = "Mr. Hammadullah Khalid"
CEO_PASSCODE: str = os.getenv("CEO_PASSCODE", "!Catch me if you can Hacker!")

SUPPORTED_MODELS: List[str] = [
    GROQ_MODEL,
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound"
]

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
DOCUMENTS_DIR = os.path.join(UPLOADS_DIR, "documents")
IMAGES_DIR = os.path.join(UPLOADS_DIR, "images")

MEMORY_FILE = os.path.join(DATA_DIR, "long_term_memory.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

SANDBOX_TIMEOUT_SECONDS = 7.0
MAX_OUTPUT_CHARS = 4000
MAX_SEARCH_RESULTS = 6
MAX_CONVERSATION_TURNS = 25
