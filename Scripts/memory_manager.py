"""
memory_manager.py — Долгосрочная Векторная Память Бота.

Архитектура:
- SQLite3 (встроен в Python, нет зависимостей) для хранения фактов и векторов.
- Jina AI Embeddings v3 (1024-dim) для векторизации текста.
- Чистая Python cosine similarity (без numpy/scipy — легкий деплой на Render).

Модуль полностью автономен и не зависит от telebot или основного скрипта.
"""

import os
import json
import math
import sqlite3
import time
import requests as http_requests
from dotenv import load_dotenv

# Load environment
load_dotenv('../Credentials.env')
load_dotenv('Credentials.env')

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_EMBED_URL = "https://api.jina.ai/v1/embeddings"
JINA_EMBED_MODEL = "jina-embeddings-v3"
EMBED_DIM = 1024  # Dimension of jina-embeddings-v3

# --- Database Setup ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.normpath(os.path.join(PROJECT_ROOT, "assistant_data.db"))

def _get_db():
    """Get database connection with WAL mode for performance."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    """Initialize database tables if they don't exist."""
    conn = _get_db()
    cursor = conn.cursor()
    
    # Long-term memory: stores facts with their vector embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fact_text TEXT NOT NULL,
            embedding_json TEXT,
            created_at REAL NOT NULL,
            source TEXT DEFAULT 'conversation'
        )
    """)
    
    # Index for fast user lookup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ltm_user 
        ON long_term_memory(user_id)
    """)
    
    # Reminders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_text TEXT NOT NULL,
            created_at REAL NOT NULL,
            remind_at REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            sent_at REAL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reminders_pending 
        ON reminders(status, remind_at)
    """)
    
    conn.commit()
    conn.close()
    print("✅ Memory DB initialized.")

# Initialize on import
init_db()


# --- Jina Embeddings ---

def get_embedding(text: str) -> list[float] | None:
    """
    Get vector embedding for a text string using Jina AI.
    Returns a list of 1024 floats, or None on failure.
    """
    if not JINA_API_KEY:
        print("⚠️ JINA_API_KEY not set, skipping embedding.")
        return None
    
    try:
        resp = http_requests.post(
            JINA_EMBED_URL,
            headers={
                "Authorization": f"Bearer {JINA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": JINA_EMBED_MODEL,
                "input": [text[:8000]],  # Limit input to avoid token overflow
                "task": "text-matching"
            },
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["data"][0]["embedding"]
        else:
            print(f"⚠️ Jina embed error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"⚠️ Jina embed exception: {e}")
        return None


# --- Pure Python Vector Math ---

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Pure Python, no numpy needed. Returns float in [-1, 1].
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


# --- Memory CRUD Operations ---

def save_memory(user_id: int, fact_text: str, source: str = "conversation") -> bool:
    """
    Save a fact to long-term memory with its vector embedding.
    Returns True on success, False on failure.
    """
    embedding = get_embedding(fact_text)
    embedding_json = json.dumps(embedding) if embedding else None
    
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO long_term_memory (user_id, fact_text, embedding_json, created_at, source) VALUES (?, ?, ?, ?, ?)",
            (user_id, fact_text, embedding_json, time.time(), source)
        )
        conn.commit()
        conn.close()
        print(f"💾 Memory saved for user {user_id}: {fact_text[:60]}...")
        return True
    except Exception as e:
        print(f"⚠️ Memory save error: {e}")
        return False


def search_memories(user_id: int, query: str, top_k: int = 3, threshold: float = 0.5) -> list[dict]:
    """
    Search long-term memory for facts relevant to the query.
    Uses vector similarity matching. Returns list of {fact_text, similarity, created_at}.
    """
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT fact_text, embedding_json, created_at FROM long_term_memory WHERE user_id = ? AND embedding_json IS NOT NULL",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"⚠️ Memory search error: {e}")
        return []
    
    if not rows:
        return []
    
    # Calculate similarities
    scored = []
    for fact_text, emb_json, created_at in rows:
        try:
            stored_embedding = json.loads(emb_json)
            sim = cosine_similarity(query_embedding, stored_embedding)
            if sim >= threshold:
                scored.append({
                    "fact_text": fact_text,
                    "similarity": round(sim, 4),
                    "created_at": created_at
                })
        except (json.JSONDecodeError, TypeError):
            continue
    
    # Sort by similarity descending, return top_k
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def get_all_memories(user_id: int, limit: int = 50) -> list[dict]:
    """Get all stored memories for a user (for debugging/display)."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, fact_text, created_at, source FROM long_term_memory WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "fact_text": r[1], "created_at": r[2], "source": r[3]} for r in rows]
    except Exception as e:
        print(f"⚠️ Get all memories error: {e}")
        return []


def delete_memory(memory_id: int) -> bool:
    """Delete a specific memory by its ID."""
    try:
        conn = _get_db()
        conn.execute("DELETE FROM long_term_memory WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Memory delete error: {e}")
        return False


def clear_user_memories(user_id: int) -> int:
    """Clear all long-term memories for a user. Returns count of deleted rows."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM long_term_memory WHERE user_id = ?", (user_id,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"🧹 Cleared {count} memories for user {user_id}")
        return count
    except Exception as e:
        print(f"⚠️ Memory clear error: {e}")
        return 0


# --- Jina Search (Hybrid Web Search) ---

def jina_search(query: str, max_results: int = 3) -> str:
    """
    Search the web using Jina Search API (s.jina.ai).
    Returns clean markdown text with search results, ready for LLM consumption.
    """
    if not JINA_API_KEY:
        return ""
    
    try:
        resp = http_requests.get(
            f"https://s.jina.ai/{query}",
            headers={
                "Authorization": f"Bearer {JINA_API_KEY}",
                "Accept": "application/json",
                "X-Retain-Images": "none"
            },
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("data", [])[:max_results]
            
            if not results:
                return ""
            
            context = "🔍 Результаты веб-поиска (Jina Search):\n"
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                content = r.get("content", "")[:500]  # Limit each result
                url = r.get("url", "")
                context += f"\n{i}. **{title}**\n{content}\n[Источник: {url}]\n"
            return context
        else:
            print(f"⚠️ Jina Search error {resp.status_code}")
            return ""
    except Exception as e:
        print(f"⚠️ Jina Search exception: {e}")
        return ""


def jina_read_url(url: str) -> str:
    """
    Read and extract clean content from a URL using Jina Reader API (r.jina.ai).
    Returns clean markdown text, ready for LLM consumption.
    """
    if not JINA_API_KEY:
        return ""
    
    try:
        resp = http_requests.get(
            f"https://r.jina.ai/{url}",
            headers={
                "Authorization": f"Bearer {JINA_API_KEY}",
                "Accept": "text/markdown",
                "X-Retain-Images": "none"
            },
            timeout=15
        )
        if resp.status_code == 200:
            content = resp.text[:5000]  # Limit to avoid token overflow
            return content
        else:
            print(f"⚠️ Jina Reader error {resp.status_code}")
            return ""
    except Exception as e:
        print(f"⚠️ Jina Reader exception: {e}")
        return ""


# --- Reminders CRUD ---

def create_reminder(user_id: int, text: str, remind_at: float) -> int | None:
    """
    Create a new reminder. Returns the reminder ID on success, None on failure.
    remind_at is a Unix timestamp (seconds since epoch).
    """
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, reminder_text, created_at, remind_at, status) VALUES (?, ?, ?, ?, 'pending')",
            (user_id, text, time.time(), remind_at)
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"⏰ Reminder #{reminder_id} created for user {user_id}: '{text[:40]}...' at {remind_at}")
        return reminder_id
    except Exception as e:
        print(f"⚠️ Create reminder error: {e}")
        return None


def get_due_reminders() -> list[dict]:
    """
    Get all pending reminders whose remind_at time has passed.
    Returns list of {id, user_id, reminder_text, remind_at}.
    """
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, reminder_text, remind_at FROM reminders WHERE status = 'pending' AND remind_at <= ?",
            (time.time(),)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "user_id": r[1], "reminder_text": r[2], "remind_at": r[3]} for r in rows]
    except Exception as e:
        print(f"⚠️ Get due reminders error: {e}")
        return []


def mark_reminder_sent(reminder_id: int) -> bool:
    """Mark a reminder as sent."""
    try:
        conn = _get_db()
        conn.execute(
            "UPDATE reminders SET status = 'sent', sent_at = ? WHERE id = ?",
            (time.time(), reminder_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ Mark reminder sent error: {e}")
        return False


def get_user_reminders(user_id: int, status: str = "pending") -> list[dict]:
    """Get all reminders for a user with given status."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, reminder_text, remind_at, status FROM reminders WHERE user_id = ? AND status = ? ORDER BY remind_at ASC",
            (user_id, status)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "reminder_text": r[1], "remind_at": r[2], "status": r[3]} for r in rows]
    except Exception as e:
        print(f"⚠️ Get user reminders error: {e}")
        return []


def cancel_reminder(reminder_id: int, user_id: int) -> bool:
    """Cancel a pending reminder. Returns True if found and cancelled."""
    try:
        conn = _get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reminders SET status = 'cancelled' WHERE id = ? AND user_id = ? AND status = 'pending'",
            (reminder_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception as e:
        print(f"⚠️ Cancel reminder error: {e}")
        return False

