"""
JARVIS Memory System — v2
─────────────────────────────────────────────────────────────────
Architecture:
  exchanges     — raw turn-by-turn log (user + assistant + timestamp)
  summaries     — rolling compressed summaries (auto-generated every N turns)
  entities      — extracted facts about the user (name, preferences, context)
  topics        — conversation topic tags for retrieval

Strategy:
  1. Every exchange saved with full text
  2. When exchanges > SUMMARY_TRIGGER, oldest batch is summarised by Ollama
     and compressed into a single summary row — raw rows deleted
  3. build_context() returns: [system_prompt] + [summaries] + [recent_raw]
     → JARVIS always has long-term compressed memory + sharp short-term detail
  4. Entity extraction runs after every exchange and upserts to entities table
     → user facts persist indefinitely regardless of summary compression
"""

import aiosqlite
import httpx
import json
import re
from datetime import datetime
from pathlib import Path

DB_PATH          = Path(__file__).parent / "jarvis_memory.db"
OLLAMA_URL       = "http://localhost:11434/api/chat"
SUMMARY_MODEL    = "llama3.2:3b"
SUMMARY_TRIGGER  = 12    # summarise when raw exchanges exceed this
SUMMARY_BATCH    = 8     # how many exchanges to compress per summary
RECENT_KEEP      = 6     # raw exchanges to always keep (never summarised)
MAX_SUMMARIES    = 5     # keep at most this many summaries in context


# ── Database setup ────────────────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS exchanges (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                content     TEXT NOT NULL,
                covers_from TEXT NOT NULL,
                covers_to   TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange_id INTEGER,
                tag        TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


# ── Core save/load ────────────────────────────────────────────────────

async def save_exchange(user_msg: str, assistant_msg: str):
    """Save one turn, then trigger background compression if needed."""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO exchanges (role, content, timestamp) VALUES (?, ?, ?)",
            ("user", user_msg, now)
        )
        await db.execute(
            "INSERT INTO exchanges (role, content, timestamp) VALUES (?, ?, ?)",
            ("assistant", assistant_msg, now)
        )
        await db.commit()

    # Fire-and-forget — don't block the response
    await maybe_summarise()
    await extract_entities(user_msg, assistant_msg)


async def load_history(limit: int = 6) -> list[dict]:
    """Return the most recent `limit` exchanges as Ollama message dicts."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT role, content FROM exchanges
               ORDER BY id DESC LIMIT ?""",
            (limit * 2,)   # *2 because each exchange = 2 rows
        ) as cur:
            rows = await cur.fetchall()
    rows.reverse()
    return [{"role": r[0], "content": r[1]} for r in rows]


async def build_context(user_message: str) -> list[dict]:
    """
    Returns the full message list for Ollama:
      [recent summaries as system context] + [recent raw exchanges] + [user turn]

    This gives JARVIS long-term memory (summaries) + sharp recall (recent turns).
    """
    context_blocks = []

    # 1. Entity facts — always injected (name, preferences, etc.)
    entities = await get_entities()
    if entities:
        facts = "\n".join(f"  • {k}: {v}" for k, v in entities.items())
        context_blocks.append({
            "role": "system",
            "content": f"KNOWN FACTS ABOUT THE USER:\n{facts}"
        })

    # 2. Rolling summaries — compressed long-term memory
    summaries = await get_recent_summaries(limit=MAX_SUMMARIES)
    if summaries:
        summary_text = "\n\n".join(
            f"[MEMORY {i+1} — {s['covers_from'][:10]} to {s['covers_to'][:10]}]\n{s['content']}"
            for i, s in enumerate(summaries)
        )
        context_blocks.append({
            "role": "system",
            "content": f"CONVERSATION HISTORY (COMPRESSED):\n{summary_text}"
        })

    # 3. Recent raw exchanges — sharp short-term recall
    recent = await load_history(limit=RECENT_KEEP)
    context_blocks += recent

    return context_blocks


# ── Summarisation engine ──────────────────────────────────────────────

async def maybe_summarise():
    """If raw exchange count exceeds trigger, compress oldest batch."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM exchanges") as cur:
            (count,) = await cur.fetchone()

    # Need: SUMMARY_BATCH compressable + RECENT_KEEP untouched
    if count < (SUMMARY_BATCH * 2) + (RECENT_KEEP * 2):
        return   # not enough yet

    compressable = count - (RECENT_KEEP * 2)
    if compressable < SUMMARY_BATCH * 2:
        return

    await _compress_oldest_batch()


async def _compress_oldest_batch():
    """Fetch oldest SUMMARY_BATCH exchanges, summarise, delete raw rows."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT id, role, content, timestamp FROM exchanges
               ORDER BY id ASC LIMIT ?""",
            (SUMMARY_BATCH * 2,)
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        return

    # Build conversation text for the LLM to summarise
    convo_lines = []
    for _, role, content, ts in rows:
        label = "Sir" if role == "user" else "JARVIS"
        convo_lines.append(f"{label}: {content}")
    convo_text = "\n".join(convo_lines)

    covers_from = rows[0][3]
    covers_to   = rows[-1][3]

    summary = await _call_ollama_summary(convo_text)
    if not summary:
        return  # don't delete if summarisation failed

    now = datetime.now().isoformat()
    ids = [r[0] for r in rows]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO summaries (content, covers_from, covers_to, created_at) VALUES (?, ?, ?, ?)",
            (summary, covers_from, covers_to, now)
        )
        placeholders = ",".join("?" * len(ids))
        await db.execute(f"DELETE FROM exchanges WHERE id IN ({placeholders})", ids)
        await db.commit()

    print(f"[MEMORY] Compressed {len(ids)//2} exchanges into summary.")


async def _call_ollama_summary(convo_text: str) -> str | None:
    """Ask Ollama to produce a compact summary of a conversation segment."""
    prompt = f"""Summarise the following conversation between a user ("Sir") and an AI assistant ("JARVIS").
Extract: key topics discussed, decisions made, facts learned about the user, and any pending tasks.
Be concise — maximum 150 words. Write in third person as a briefing note.

CONVERSATION:
{convo_text}

SUMMARY:"""

    payload = {
        "model": SUMMARY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": 200, "temperature": 0.3}
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(OLLAMA_URL, json=payload)
            data = r.json()
            return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"[MEMORY] Summary generation failed: {e}")
        return None


async def get_recent_summaries(limit: int = MAX_SUMMARIES) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT content, covers_from, covers_to FROM summaries
               ORDER BY id DESC LIMIT ?""", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    rows.reverse()
    return [{"content": r[0], "covers_from": r[1], "covers_to": r[2]} for r in rows]


# ── Entity extraction ─────────────────────────────────────────────────

ENTITY_PATTERNS = [
    # Name: "call me X", "my name is X", "I'm X"
    (r"(?:call me|my name is|i'm|i am)\s+([A-Za-z]+)", "user_name"),
    # Location: "I'm in X", "I live in X"
    (r"(?:i(?:'m| am) in|i live in|based in|from)\s+([A-Za-z\s]+?)(?:\.|,|$)", "user_location"),
    # Occupation: "I'm a X", "I work as X", "I study X"
    (r"(?:i(?:'m| am) an?\s|i work as an?\s|i study\s)([A-Za-z\s]+?)(?:\.|,|$)", "user_occupation"),
    # Project mentions: "working on X", "my project X"
    (r"(?:working on|my project(?:s)? (?:is|are)?)\s+([A-Za-z0-9\s\-_]+?)(?:\.|,|$)", "current_project"),
]

async def extract_entities(user_msg: str, assistant_msg: str):
    """Run regex patterns over the user message and upsert any found facts."""
    now = datetime.now().isoformat()
    found = {}
    lower = user_msg.lower()
    for pattern, key in ENTITY_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            val = m.group(1).strip().title()
            if len(val) > 1:
                found[key] = val

    if not found:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        for key, value in found.items():
            await db.execute(
                """INSERT INTO entities (key, value, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, value, now)
            )
        await db.commit()

    for k, v in found.items():
        print(f"[MEMORY] Entity upsert — {k}: {v}")


async def get_entities() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key, value FROM entities") as cur:
            rows = await cur.fetchall()
    return {r[0]: r[1] for r in rows}


async def set_entity(key: str, value: str):
    """Manually set a persistent fact about the user."""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO entities (key, value, updated_at) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value, now)
        )
        await db.commit()


# ── Stats + management ────────────────────────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM exchanges") as cur:
            (exchanges,) = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM summaries") as cur:
            (summaries,) = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM entities") as cur:
            (entities,) = await cur.fetchone()
    return {
        "raw_exchanges":  exchanges // 2,
        "summaries":      summaries,
        "known_entities": entities,
        "total_turns":    (exchanges // 2) + (summaries * SUMMARY_BATCH),
    }


async def clear_history():
    """Wipe exchanges and summaries. Preserve entities (user facts)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM exchanges")
        await db.execute("DELETE FROM summaries")
        await db.commit()


async def clear_all():
    """Full wipe including entities."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM exchanges")
        await db.execute("DELETE FROM summaries")
        await db.execute("DELETE FROM entities")
        await db.commit()
