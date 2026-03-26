"""
FastAPI backend for Multi-Agent Customer Support System.
Provides REST API and SSE streaming for real-time agent updates.
"""

import os
import csv
import hashlib
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

import database as db
import knowledge_base as kb
import memory as mem
import agents

load_dotenv()

# ─────────────────────────────────────────────
# CSV-based User Storage
# ─────────────────────────────────────────────

USERS_CSV = Path(__file__).parent / "users.csv"
CSV_FIELDS = ["id", "name", "email", "password_hash"]


def _ensure_csv():
    """Create users.csv with headers if it doesn't exist."""
    if not USERS_CSV.exists():
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


def _hash_password(password: str) -> str:
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _read_users() -> list[dict]:
    """Read all users from CSV."""
    _ensure_csv()
    with open(USERS_CSV, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_user(user: dict):
    """Append a new user to CSV."""
    _ensure_csv()
    with open(USERS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(user)


def _find_user_by_email(email: str) -> Optional[dict]:
    """Find a user by email (case-insensitive)."""
    users = _read_users()
    for u in users:
        if u["email"].lower() == email.lower():
            return u
    return None


# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and knowledge base on startup."""
    print("[*] Initializing Multi-Agent Customer Support System...")
    
    try:
        # Initialize database
        db.init_db()
        db.seed_customers()
        db.seed_orders()
        print("[+] Database initialized")
    except Exception as e:
        print(f"[!] Database initialization error: {e}")
    
    try:
        # Initialize ChromaDB knowledge base
        kb.seed_knowledge_base()
        print("[+] Knowledge base initialized")
    except Exception as e:
        print(f"[!] Knowledge base initialization error: {e}")
    
    print("[+] System ready!")
    yield
    print("[~] Shutting down...")


app = FastAPI(
    title="Multi-Agent Customer Support API",
    description="LangGraph-powered multi-agent system with routing, memory, and escalation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Render deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    category: Optional[str] = None
    agent: Optional[str] = None
    nodes_fired: list[str] = []
    escalation_ticket: Optional[str] = None
    resolved: bool = True


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ─────────────────────────────────────────────
# Auth Endpoints
# ─────────────────────────────────────────────

@app.post("/auth/signup")
async def signup(request: SignupRequest):
    """Register a new user. Data stored in CSV."""
    name = request.name.strip()
    email = request.email.strip().lower()
    
    if not name or not email or not request.password:
        raise HTTPException(status_code=400, detail="All fields are required.")
    
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    # Check for existing user
    if _find_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    
    user_id = str(uuid.uuid4())[:8]
    user_record = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": _hash_password(request.password),
    }
    _write_user(user_record)
    
    return {
        "message": "Account created successfully.",
        "user": {"id": user_id, "name": name, "email": email},
    }


@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate a user against CSV store."""
    email = request.email.strip().lower()
    
    user = _find_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if user["password_hash"] != _hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    return {
        "message": "Login successful.",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Multi-Agent Customer Support System",
        "version": "1.0.0",
        "agents": ["billing", "technical", "returns", "general"],
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — runs the agent pipeline."""
    try:
        result = await agents.run_agent(request.session_id, request.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/stream/{session_id}")
async def stream_events(session_id: str):
    """SSE endpoint for real-time agent pipeline updates."""
    async def event_generator():
        yield {
            "event": "connected",
            "data": {"session_id": session_id, "timestamp": "connected"}
        }
        
        import asyncio
        while True:
            await asyncio.sleep(15)
            yield {
                "event": "heartbeat",
                "data": {"status": "alive"}
            }
    
    return EventSourceResponse(event_generator())


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    history = mem.load_session_context(session_id)
    return {"session_id": session_id, "messages": history}


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear session memory."""
    mem.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/sessions/sample-data")
async def get_sample_data():
    """Get sample customer and order data for testing."""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT email, name, plan FROM customers LIMIT 5")
    customers = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT order_id, product, status FROM orders LIMIT 5")
    orders = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "sample_customers": customers,
        "sample_orders": orders,
        "hint": "Use these emails and order IDs to test the system"
    }


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get escalation ticket details."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/knowledge-base/search")
async def search_knowledge_base(query: str, limit: int = 3):
    """Search the technical knowledge base."""
    results = kb.query_knowledge_base(query, n_results=limit)
    return {"query": query, "results": results}


@app.get("/health")
async def health_check():
    """Detailed health check with service status."""
    redis_status = "connected" if mem.get_redis_client() else "fallback (in-memory)"
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
        collection = client.get_collection("technical_kb")
        kb_count = collection.count()
        kb_status = f"ready ({kb_count} documents)"
    except Exception:
        kb_status = "not initialized"
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0]
    conn.close()
    
    return {
        "status": "healthy",
        "services": {
            "redis": redis_status,
            "chromadb": kb_status,
            "sqlite": f"ready ({customer_count} customers, {order_count} orders)",
            "groq_api": "configured" if os.getenv("GROQ_API_KEY") else "missing"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
