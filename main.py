"""
NexusAI Studio - Master Production FastAPI Server (Real Google OAuth 2.0 Integration).
"""

import os
import sys
import time
import httpx

current_dir = os.path.dirname(os.path.abspath(__file__))
for sub in [current_dir, os.path.join(current_dir, "nexus_ai"), os.getcwd(), os.path.join(os.getcwd(), "nexus_ai")]:
    if os.path.exists(sub) and sub not in sys.path:
        sys.path.insert(0, sub)

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GOOGLE_CLIENT_ID,
    HOST,
    PORT,
    COMPANY_NAME,
    CEO_NAME,
    CEO_PASSCODE
)
from conversation_manager import PersistentConversationManager
from agent.orchestrator import ReActAgent
from tools.code_sandbox import PythonCodeSandbox

app = FastAPI(
    title="NexusAI Studio — 13-Pillar Autonomous Agentic Operating System",
    description="Multi-User AI OS with Real Google OAuth 2.0, Persistent SQLite, Python Sandbox & Vision",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
conversation_manager = PersistentConversationManager()
agent = ReActAgent()
direct_sandbox = PythonCodeSandbox()

# Auth Request Models
class GoogleRealAuthRequest(BaseModel):
    credential: str # Google JWT ID token

class AgentRunRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    is_ceo: Optional[bool] = False
    has_attachments: Optional[bool] = False
    attached_doc_id: Optional[str] = None
    has_image: Optional[bool] = False
    image_metadata: Optional[Dict[str, Any]] = None
    selected_model: Optional[str] = "auto"

class CodeExecuteRequest(BaseModel):
    code: str

class DeepResearchRequest(BaseModel):
    topic: str

class MemoryRequest(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"
    user_id: Optional[str] = "default_user"

class CEOAuthRequest(BaseModel):
    passcode: str

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "system": "NexusAI 13-Pillar Master OS v6.0",
        "company": COMPANY_NAME,
        "founder_ceo": CEO_NAME,
        "default_model": GROQ_MODEL,
        "google_oauth_enabled": bool(GOOGLE_CLIENT_ID),
        "database": "Persistent SQLite (data/nexus_ai.db)"
    }

@app.get("/api/auth/config")
def get_auth_config():
    """Returns Google OAuth Client ID if configured."""
    return {
        "google_client_id": GOOGLE_CLIENT_ID or None,
        "company_name": COMPANY_NAME,
        "ceo_name": CEO_NAME
    }

# ----------------- Real Google OAuth 2.0 Endpoint ----------------- #
@app.post("/api/auth/google")
async def verify_google_oauth(req: GoogleRealAuthRequest):
    """
    Verifies real cryptographic Google ID token directly with Google's OAuth2 API.
    Extracts verified real email, name, and profile picture.
    """
    if not req.credential:
        raise HTTPException(status_code=400, detail="Missing Google credential token.")

    try:
        # Verify ID token with Google's official endpoint
        google_token_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(google_token_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Google authentication failed: Token is invalid or expired.")
            
            token_info = resp.json()
            email = token_info.get("email")
            name = token_info.get("name") or "Google User"
            picture = token_info.get("picture")
            email_verified = token_info.get("email_verified") in (True, "true")

            if not email or not email_verified:
                raise HTTPException(status_code=400, detail="Google account email is unverified.")

            user = conversation_manager.get_or_create_google_user(email=email, name=name, picture=picture)
            return {
                "status": "success",
                "user": user,
                "picture": picture,
                "message": f"Successfully signed in with Google as {name} ({email})!"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google verification error: {str(e)}")

@app.get("/api/admin/users")
def get_all_users_admin(is_ceo: bool = False):
    """CEO-only: Returns the registered user directory stored on your computer."""
    if not is_ceo:
        raise HTTPException(status_code=403, detail="Access Denied: Executive CEO privileges required.")
    return {"users": conversation_manager.list_all_users_for_admin()}

@app.post("/api/auth/ceo")
def authenticate_ceo(req: CEOAuthRequest):
    if req.passcode.strip() == CEO_PASSCODE.strip():
        return {
            "authenticated": True,
            "role": "CEO",
            "name": CEO_NAME,
            "company": COMPANY_NAME,
            "message": f"Welcome back, Boss! Executive CEO Master Access unlocked for {CEO_NAME}."
        }
    raise HTTPException(status_code=401, detail="Authentication Failed: Invalid CEO Executive Passcode.")

# ----------------- Agent Execution Endpoints ----------------- #
@app.post("/api/agent/run")
async def run_agent(req: AgentRunRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_id = req.user_id or "default_user"
    session = conversation_manager.get_or_create_session(user_id=user_id, session_id=req.session_id)
    session_id = session["session_id"]

    history = conversation_manager.get_llm_messages(user_id=user_id, session_id=session_id, max_turns=10)

    try:
        result = await agent.run(
            query=query,
            conversation_history=history,
            user_id=user_id,
            is_ceo_authenticated=bool(req.is_ceo),
            has_attachments=bool(req.has_attachments),
            attached_doc_id=req.attached_doc_id,
            image_metadata=req.image_metadata if req.has_image else None,
            selected_model=req.selected_model if req.selected_model != "auto" else None
        )
    except Exception as e:
        print(f"[Agent Execution Error]: {e}")
        result = {
            "query": query,
            "answer": f"I encountered an issue processing your request: {str(e)}. Please try again.",
            "intent": "error",
            "trigger_ceo_lockout": False,
            "active_model": "NexusAI Fallback",
            "tool_steps": [],
            "images": [],
            "sources": [],
            "dossier_data": None,
            "verification": {"verified": False, "flags": [str(e)]},
            "model_used": "NexusAI Core",
            "latency_ms": 80.0
        }

    conversation_manager.add_user_turn(user_id=user_id, session_id=session_id, content=query)
    conversation_manager.add_assistant_turn(
        user_id=user_id,
        session_id=session_id,
        content=result["answer"],
        search_executed=bool(result.get("sources")),
        sources=result.get("sources", [])
    )

    return {
        "session_id": session_id,
        "query": query,
        "answer": result["answer"],
        "intent": result.get("intent", "direct_chat"),
        "trigger_ceo_lockout": result.get("trigger_ceo_lockout", False),
        "active_model": result.get("active_model"),
        "tool_steps": result.get("tool_steps", []),
        "images": result.get("images", []),
        "sources": result.get("sources", []),
        "dossier_data": result.get("dossier_data"),
        "verification": result.get("verification"),
        "model_used": result.get("model_used", "NexusAI Core"),
        "latency_ms": result.get("latency_ms", 100.0)
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = Form("default_user")):
    try:
        contents = await file.read()
        parsed = agent.doc_processor.process_file(filename=file.filename, file_bytes=contents)
        
        agent.rag_engine.add_document(
            doc_id=parsed["file_id"],
            doc_name=parsed["filename"],
            content=parsed["content"],
            metadata={**parsed["metadata"], "user_id": user_id}
        )

        return {
            "status": "success",
            "file_id": parsed["file_id"],
            "filename": parsed["filename"],
            "metadata": parsed["metadata"],
            "df_preview": parsed.get("df_preview"),
            "chunks_count": len([c for c in agent.rag_engine.chunks if c.doc_id == parsed["file_id"]])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        analysis = agent.vision_analyzer.analyze_image(filename=file.filename, image_bytes=contents)
        return {
            "status": "success",
            "image": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis error: {str(e)}")

@app.get("/api/documents")
def list_documents(user_id: Optional[str] = "default_user"):
    return {
        "documents": [
            {
                "doc_id": doc["doc_id"],
                "doc_name": doc["doc_name"],
                "metadata": doc["metadata"],
                "added_at": doc["added_at"]
            }
            for doc in agent.rag_engine.documents.values()
            if doc["metadata"].get("user_id") in (user_id, "default_user", None)
        ],
        "total_chunks": len(agent.rag_engine.chunks)
    }

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    success = agent.rag_engine.remove_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "message": f"Removed document: {doc_id}"}

@app.post("/api/deep_research")
async def trigger_deep_research(req: DeepResearchRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
    return await agent.deep_research.execute_dossier_investigation(topic)

@app.post("/api/sandbox/execute")
def execute_code(req: CodeExecuteRequest):
    return direct_sandbox.execute(req.code)

@app.get("/api/memory")
def get_memories(user_id: Optional[str] = "default_user"):
    return {"memories": agent.memory_vault.recall(user_id or "default_user")}

@app.post("/api/memory")
def add_memory(req: MemoryRequest):
    return agent.memory_vault.remember(req.user_id or "default_user", req.key, req.value, req.category or "general")

@app.delete("/api/memory/{key}")
def delete_memory(key: str, user_id: Optional[str] = "default_user"):
    success = agent.memory_vault.forget(user_id or "default_user", key)
    if not success:
        raise HTTPException(status_code=404, detail="Memory key not found")
    return {"status": "success", "message": f"Forgotten: {key}"}

@app.get("/api/sessions")
def list_sessions(user_id: Optional[str] = "default_user"):
    return {"sessions": conversation_manager.list_sessions(user_id or "default_user")}

@app.get("/api/sessions/{session_id}")
def get_session_history(session_id: str, user_id: Optional[str] = "default_user"):
    session = conversation_manager.get_session_history(user_id or "default_user", session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, user_id: Optional[str] = "default_user"):
    success = conversation_manager.delete_session(user_id or "default_user", session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "message": "Session deleted"}

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"message": "NexusAI Studio API is running"})
