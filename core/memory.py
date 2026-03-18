"""
memory.py — JARVIS MKIII Memory System
Powered by Hindsight — agent memory that learns.
Replaces the old flat SQLite save_exchange / build_context system.

Three operations:
    retain  — store a new memory
    recall  — retrieve relevant memories
    reflect — deep analysis of memory patterns

Hindsight runs locally via Docker on port 8888.
100% offline — Ollama as the LLM provider.
"""

import asyncio
import httpx
import json
import sqlite3
import os
from datetime import datetime
from typing import Optional

HINDSIGHT_URL = "http://localhost:8888"
BANK_ID       = "khalid"   # Memory bank ID — one per user

# ── Fallback SQLite (used if Hindsight is unavailable) ────────────────
FALLBACK_DB = os.path.expanduser("~/.jarvis/memory_fallback.db")


class Memory:
    def __init__(self):
        self._hindsight_available = False
        self._init_fallback_db()
        print("[MEMORY] Memory system initialized.")

    def _init_fallback_db(self):
        """Initialize SQLite fallback for when Hindsight is offline."""
        os.makedirs(os.path.dirname(FALLBACK_DB), exist_ok=True)
        conn = sqlite3.connect(FALLBACK_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exchanges (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT,
                content   TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                key       TEXT PRIMARY KEY,
                value     TEXT,
                updated   TEXT
            )
        """)
        conn.commit()
        conn.close()

    async def _check_hindsight(self) -> bool:
        """Check if Hindsight is running."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{HINDSIGHT_URL}/health")
                self._hindsight_available = r.status_code == 200
        except Exception:
            self._hindsight_available = False
        return self._hindsight_available

    # ── Core API ──────────────────────────────────────────────────────

    async def retain(self, content: str, context: str = "") -> bool:
        """
        Store a new memory in Hindsight.
        Falls back to SQLite if Hindsight is unavailable.
        """
        await self._check_hindsight()

        if self._hindsight_available:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {"bank_id": BANK_ID, "content": content}
                    if context:
                        payload["context"] = context
                    r = await client.post(f"{HINDSIGHT_URL}/retain", json=payload)
                    if r.status_code == 200:
                        return True
            except Exception as e:
                print(f"[MEMORY] Hindsight retain error: {e}")

        # Fallback to SQLite
        try:
            conn = sqlite3.connect(FALLBACK_DB)
            conn.execute(
                "INSERT INTO exchanges (role, content, timestamp) VALUES (?, ?, ?)",
                ("memory", content, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[MEMORY] Fallback retain error: {e}")
            return False

    async def recall(self, query: str, limit: int = 10) -> list:
        """
        Retrieve memories relevant to a query.
        Uses 4-strategy parallel retrieval (semantic + keyword + graph + temporal).
        Falls back to SQLite keyword search.
        """
        await self._check_hindsight()

        if self._hindsight_available:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.post(f"{HINDSIGHT_URL}/recall", json={
                        "bank_id": BANK_ID,
                        "query":   query,
                        "limit":   limit,
                    })
                    if r.status_code == 200:
                        data = r.json()
                        return data.get("memories", [])
            except Exception as e:
                print(f"[MEMORY] Hindsight recall error: {e}")

        # Fallback to SQLite
        try:
            conn = sqlite3.connect(FALLBACK_DB)
            rows = conn.execute(
                "SELECT content FROM exchanges ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            conn.close()
            return [{"content": r[0]} for r in rows]
        except Exception as e:
            print(f"[MEMORY] Fallback recall error: {e}")
            return []

    async def reflect(self, query: str) -> str:
        """
        Deep reflection — JARVIS forms insights and patterns.
        Used for morning briefings and complex analysis.
        Falls back to a summary of recent exchanges.
        """
        await self._check_hindsight()

        if self._hindsight_available:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.post(f"{HINDSIGHT_URL}/reflect", json={
                        "bank_id": BANK_ID,
                        "query":   query,
                    })
                    if r.status_code == 200:
                        data = r.json()
                        return data.get("reflection", "")
            except Exception as e:
                print(f"[MEMORY] Hindsight reflect error: {e}")

        # Fallback
        memories = await self.recall(query, limit=5)
        if memories:
            return " | ".join(m.get("content", "")[:100] for m in memories)
        return ""

    # ── Context builder (drop-in replacement for old build_context) ────
    async def build_context(self, user_message: str) -> list:
        """
        Build conversation context for the LLM.
        Compatible with the old build_context() return format.
        Returns a list of {role, content} dicts.
        """
        memories = await self.recall(user_message, limit=8)
        context  = []

        for m in memories:
            content = m.get("content", "").strip()
            if not content:
                continue
            # Inject as system context
            context.append({
                "role":    "system",
                "content": f"[MEMORY] {content}"
            })

        # Also inject entity facts
        entities = await self.get_entities()
        if entities:
            facts = " | ".join(f"{k}: {v}" for k, v in entities.items())
            context.insert(0, {
                "role":    "system",
                "content": f"[KNOWN FACTS] {facts}"
            })

        return context

    # ── Exchange logging (drop-in for old save_exchange) ──────────────
    async def save_exchange(self, user_msg: str, assistant_msg: str):
        """Log a conversation exchange to memory."""
        combined = f"User said: {user_msg} | JARVIS responded: {assistant_msg}"
        await self.retain(combined, context="conversation")

    # ── Entity management ─────────────────────────────────────────────
    async def set_entity(self, key: str, value: str):
        """Store a persistent fact about the user."""
        await self.retain(f"{key}: {value}", context="entity_fact")
        # Also store in SQLite for fast local access
        try:
            conn = sqlite3.connect(FALLBACK_DB)
            conn.execute(
                "INSERT OR REPLACE INTO entities (key, value, updated) VALUES (?, ?, ?)",
                (key, value, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MEMORY] Entity store error: {e}")

    async def get_entities(self) -> dict:
        """Retrieve all persistent user facts."""
        try:
            conn  = sqlite3.connect(FALLBACK_DB)
            rows  = conn.execute("SELECT key, value FROM entities").fetchall()
            conn.close()
            return {r[0]: r[1] for r in rows}
        except Exception:
            return {}

    async def clear_history(self):
        """Clear conversation history. Entities are preserved."""
        try:
            conn = sqlite3.connect(FALLBACK_DB)
            conn.execute("DELETE FROM exchanges")
            conn.commit()
            conn.close()
            print("[MEMORY] History cleared — entities preserved.")
        except Exception as e:
            print(f"[MEMORY] Clear error: {e}")

    async def get_stats(self) -> dict:
        """Return memory statistics."""
        try:
            conn      = sqlite3.connect(FALLBACK_DB)
            exchanges = conn.execute("SELECT COUNT(*) FROM exchanges").fetchone()[0]
            entities  = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            conn.close()
            return {
                "hindsight": self._hindsight_available,
                "exchanges": exchanges,
                "entities":  entities,
                "bank_id":   BANK_ID,
            }
        except Exception:
            return {"hindsight": self._hindsight_available}


# ── Module-level helpers (backward compatible with old memory.py API) ─
_memory = Memory()

async def init_db():
    """Drop-in for old init_db() — memory already initialized."""
    available = await _memory._check_hindsight()
    if available:
        print("[MEMORY] Hindsight connected — full memory active.")
    else:
        print("[MEMORY] Hindsight offline — SQLite fallback active.")

async def save_exchange(user_msg: str, assistant_msg: str):
    await _memory.save_exchange(user_msg, assistant_msg)

async def build_context(user_message: str) -> list:
    return await _memory.build_context(user_message)

async def load_history():
    return await _memory.recall("recent conversations", limit=20)

async def clear_history():
    await _memory.clear_history()

async def get_stats() -> dict:
    return await _memory.get_stats()

async def get_entities() -> dict:
    return await _memory.get_entities()

async def set_entity(key: str, value: str):
    await _memory.set_entity(key, value)

async def recall(query: str, limit: int = 10) -> list:
    return await _memory.recall(query, limit)
