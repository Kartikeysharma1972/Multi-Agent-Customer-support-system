"""
Redis-based session memory for the Multi-Agent Customer Support System.
Stores conversation context across turns with TTL for cleanup.
"""

import json
import os
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SESSION_TTL = 3600  # 1 hour TTL for sessions
MAX_MESSAGES = 20   # Keep last 20 messages per session


def get_redis_client():
    """Get Redis client with fallback to in-memory dict."""
    try:
        import redis
        client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


# In-memory fallback when Redis is unavailable
_memory_store: dict = {}


def save_session_context(session_id: str, messages: list) -> bool:
    """Save session messages to Redis."""
    client = get_redis_client()
    key = f"session:{session_id}:messages"

    # Keep only last MAX_MESSAGES
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]

    if client:
        try:
            client.setex(key, SESSION_TTL, json.dumps(messages))
            return True
        except Exception as e:
            print(f"Redis save error: {e}")

    # Fallback to memory
    _memory_store[key] = messages
    return True


def load_session_context(session_id: str) -> list:
    """Load session messages from Redis."""
    client = get_redis_client()
    key = f"session:{session_id}:messages"

    if client:
        try:
            data = client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis load error: {e}")

    # Fallback to memory
    return _memory_store.get(key, [])


def append_message(session_id: str, role: str, content: str, agent_type: str = None):
    """Append a single message to session history."""
    messages = load_session_context(session_id)
    messages.append({
        "role": role,
        "content": content,
        "agent_type": agent_type
    })
    save_session_context(session_id, messages)


def get_session_metadata(session_id: str) -> dict:
    """Get metadata about a session."""
    client = get_redis_client()
    key = f"session:{session_id}:meta"

    if client:
        try:
            data = client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass

    return _memory_store.get(key, {
        "session_id": session_id,
        "attempt_count": {},
        "last_agent": None
    })


def update_session_metadata(session_id: str, metadata: dict):
    """Update session metadata."""
    client = get_redis_client()
    key = f"session:{session_id}:meta"

    if client:
        try:
            client.setex(key, SESSION_TTL, json.dumps(metadata))
            return
        except Exception:
            pass

    _memory_store[key] = metadata


def increment_attempt_count(session_id: str, agent_type: str) -> int:
    """Increment and return the attempt count for an agent in a session."""
    meta = get_session_metadata(session_id)
    attempts = meta.get("attempt_count", {})
    attempts[agent_type] = attempts.get(agent_type, 0) + 1
    meta["attempt_count"] = attempts
    update_session_metadata(session_id, meta)
    return attempts[agent_type]


def clear_session(session_id: str):
    """Clear all session data."""
    client = get_redis_client()
    keys = [f"session:{session_id}:messages", f"session:{session_id}:meta"]

    if client:
        try:
            client.delete(*keys)
            return
        except Exception:
            pass

    for key in keys:
        _memory_store.pop(key, None)
