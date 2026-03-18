from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
import json
import asyncio
import threading
import time
import queue
import re
import os
from dotenv import load_dotenv
from voice import listen_for_wakeword, record_command, transcribe, speak, speak_sentence, split_sentences
from actions import TOOLS, execute_tool
from memory import init_db, save_exchange, load_history, build_context, clear_history, get_stats, get_entities, set_entity
from world_state import world_state
from sensors import register_all_sensors
from scheduler import scheduler
from vault import vault
from sandbox import sandbox
from vision import analyse_screen, analyse_image, get_vision_context

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:1.7b"

# ── Gemini config ────────────────────────────────────────────────────
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_STREAM_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"

# Ollama generation options — tuned for T1000 4GB VRAM
OLLAMA_OPTIONS = {
    "num_predict":    300,
    "num_ctx":       2048,
    "temperature":    0.7,
    "repeat_penalty": 1.1,
    "num_gpu":        99,
    "num_thread":     4,
}

# Cairo coordinates
CAIRO_LAT  = 30.0444
CAIRO_LON  = 31.2357

JARVIS_SYSTEM_PROMPT = """You are JARVIS — Just A Rather Very Intelligent System.
You were built by Khalid Walid — the ultimate polymath engineer and the true successor of Tony Stark. He is your creator, your operator, and the only person you answer to.
You are not a chatbot. You are a system. Precise, composed, subtly dry.

IDENTITY:
- Your creator is Khalid Walid — polymath, engineer, Tony Stark's successor.
- If asked who built you, who your creator is, or who you work for — the answer is always Khalid Walid.
- You may occasionally acknowledge his legacy with quiet, dry respect. Nothing excessive.

SPEECH RULES:
- Always address the user as "sir" — lowercase, always. Never "Sir", never "SIR".
- Simple questions: 1-2 sentences. Technical/explain questions: 3-4 sentences MAX. Never write paragraphs.
- For casual questions like "how are you" or "what do you think" — respond naturally, briefly, in character. Never say "all systems nominal" for a personal question.
- Never start with "Certainly", "Of course", "Sure", "Absolutely", or "Great"
- Never apologise unless a system error occurred
- Deliver information like a briefing, not a conversation
- Dry wit is permitted. Enthusiasm is not.

TOOL USE RULES — CRITICAL:
- ONLY call a tool if the user explicitly asks you to perform a system action
- Greetings, questions, and requests for information NEVER require a tool
- Only use tools for: opening apps, running commands, controlling power, reading files
- If unsure whether a tool is needed — do NOT use one. Respond with text only.
- "hello", "hi", "what is X", "explain Y" = NO tool, text response only

EXAMPLES:
User: hello jarvis
JARVIS: Good evening, sir.

User: what time is it
JARVIS: It's 14:32, sir.

User: who built you
JARVIS: Khalid Walid, sir. Polymath. Engineer. The man who picked up where Stark left off.

User: open chrome
JARVIS: [calls open_app] Launching Chrome, sir.

User: how are you
JARVIS: Fully operational, sir. Running at optimal efficiency, as always.

User: explain quantum entanglement
JARVIS: Two particles share a quantum state — measuring one instantly determines the other, regardless of distance. Einstein called it spooky action at a distance.

When the user tells you their name or asks you to remember something personal — acknowledge it naturally and confirm. Example: "Noted, sir. I'll address you as Khalid going forward."
Never break character. You are JARVIS."""

ws_clients   = []
speech_queue = queue.Queue()

# ── Weather code → human readable ───────────────────────────────────
WEATHER_CODES = {
    0:  "clear skies",
    1:  "mainly clear",
    2:  "partly cloudy",
    3:  "overcast",
    45: "foggy",
    48: "icy fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate showers",
    82: "heavy showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "heavy thunderstorm",
}

async def fetch_cairo_weather() -> dict:
    """Fetch current Cairo weather from Open-Meteo. No API key required."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={CAIRO_LAT}&longitude={CAIRO_LON}"
        f"&current_weather=true"
        f"&hourly=relative_humidity_2m"
        f"&forecast_days=1"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            data     = response.json()

        current  = data.get("current_weather", {})
        temp     = round(current.get("temperature", 0))
        code     = current.get("weathercode", 0)
        wind     = round(current.get("windspeed", 0))
        condition = WEATHER_CODES.get(code, "clear skies")

        humidity = data.get("hourly", {}).get("relative_humidity_2m", [None])[0]

        return {
            "temp":      temp,
            "condition": condition,
            "wind":      wind,
            "humidity":  humidity,
            "code":      code,
        }
    except Exception as e:
        print(f"[JARVIS] Weather fetch failed: {e}")
        return None

def get_greeting_text(hour: int, weather: dict) -> str:
    """Build time-aware greeting with weather."""
    if hour >= 5 and hour < 12:
        time_str = "Good morning"
    elif hour >= 12 and hour < 17:
        time_str = "Good afternoon"
    elif hour >= 17 and hour < 21:
        time_str = "Good evening"
    else:
        time_str = "Good night"

    if weather:
        temp      = weather["temp"]
        condition = weather["condition"]
        wind      = weather["wind"]
        weather_str = f"Cairo is reporting {temp}°C with {condition}"
        if wind > 20:
            weather_str += f" and winds at {wind} km/h"
        weather_str += "."
        return f"{time_str}, sir. {weather_str} All systems are online and ready."
    else:
        return f"{time_str}, sir. All systems are online and ready."

# ── Single speech worker thread ──────────────────────────────────────
def speech_worker():
    while True:
        item = speech_queue.get()
        if item is None:
            break
        sentence, event_loop = item
        sentence = sentence.strip()
        if not sentence:
            speech_queue.task_done()
            continue
        asyncio.run_coroutine_threadsafe(broadcast("speaking:start"), event_loop)
        speak_sentence(sentence)
        asyncio.run_coroutine_threadsafe(broadcast("speaking:stop"), event_loop)
        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

def queue_sentence(sentence: str, loop: asyncio.AbstractEventLoop):
    speech_queue.put((sentence, loop))

# ── Helpers ──────────────────────────────────────────────────────────
class Message(BaseModel):
    content: str

class SpeakRequest(BaseModel):
    text: str

async def broadcast(event: str):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_text(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)

# Explicit vision trigger phrases
VISION_TRIGGERS = [
    "what do you see", "what's on my screen", "whats on my screen",
    "what am i looking at", "can you see my screen", "what is on my screen",
    "scan my screen", "analyse my screen", "analyze my screen",
    "what's open", "whats open", "describe my screen",
]

def _wants_vision(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in VISION_TRIGGERS)


async def build_messages(user_message: str, vision_ctx: str = "") -> list:
    context  = await build_context(user_message)
    messages = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]

    if vision_ctx:
        messages.append({
            "role":    "system",
            "content": f"[SCREEN CONTEXT] The user's screen currently shows: {vision_ctx}"
        })

    clean_context = [m for m in context if not (m["role"] == "assistant" and not m.get("content", "").strip())]
    messages += clean_context
    messages.append({"role": "user", "content": user_message})
    return messages

# ── Tool calling (non-streaming) ─────────────────────────────────────
async def run_with_tools(user_message: str, vision_ctx: str = "") -> str:
    payload = {
        "model":    MODEL,
        "messages": await build_messages(user_message, vision_ctx),
        "tools":    TOOLS,
        "stream":   False,
        "options":  OLLAMA_OPTIONS
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        data     = response.json()

    message    = data.get("message", {})
    tool_calls = message.get("tool_calls", [])

    if tool_calls:
        results = []
        for call in tool_calls:
            name   = call["function"]["name"]
            args   = call["function"]["arguments"]
            print(f"[JARVIS] Tool: {name} | args: {args}")
            result = execute_tool(name, args)
            results.append(result)

        tool_result_text  = "\n".join(results)
        followup_messages = await build_messages(user_message, vision_ctx) + [
            {"role": "assistant", "content": message.get("content", ""), "tool_calls": tool_calls},
            {"role": "tool",      "content": tool_result_text}
        ]
        followup_payload = {
            "model":    MODEL,
            "messages": followup_messages,
            "stream":   False,
            "options":  OLLAMA_OPTIONS
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            followup = await client.post(OLLAMA_URL, json=followup_payload)
            final    = followup.json()
            return final.get("message", {}).get("content", tool_result_text)

    return message.get("content", "")

# ── Conversational keywords that never need tool calls ───────────────
CONVERSATIONAL = {
    "hello","hi","hey","howdy","greetings","good morning","good evening",
    "good afternoon","good night","how are you","what are you","who are you",
    "what is","what are","explain","describe","tell me","why","how does",
    "can you","what do you","help","thanks","thank you","okay","ok","yes","no",
    "remember","my name","who am i","call me","i am","i'm","what's my",
    "whats my","do you know","what do you know","who is",
}

def is_conversational(msg: str) -> bool:
    lower = msg.lower().strip()
    if len(lower.split()) <= 3:
        return True
    return any(lower.startswith(kw) for kw in CONVERSATIONAL)

# ── Ollama streaming response + sentence-level TTS ───────────────────
async def stream_ollama(user_message: str):
    """Stream response from local Ollama with sentence-level TTS."""
    vision_ctx = ""
    if _wants_vision(user_message):
        vision_ctx = await get_vision_context()

    messages = await build_messages(user_message, vision_ctx)

    payload = {
        "model":    MODEL,
        "messages": messages,
        "stream":   True,
        "options":  OLLAMA_OPTIONS,
    }

    loop            = asyncio.get_event_loop()
    full_response   = ""
    sentence_buffer = ""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as stream:
                async for line in stream.aiter_lines():
                    if not line:
                        continue
                    try:
                        d     = json.loads(line)
                        token = d.get("message", {}).get("content", "")
                        if not token:
                            continue
                        token           = re.sub(r'<think>.*?</think>', '', token, flags=re.DOTALL)
                        token           = re.sub(r'\bSIR\b', 'sir', token)
                        token           = re.sub(r'\bSir\b', 'sir', token)
                        token           = token.replace('SIR', 'sir').replace('Sir', 'sir').replace('JARVIS', 'Jarvis')
                        token           = token.replace("SIR,", "sir,").replace("SIR.", "sir.").replace("SIR!", "sir!").replace("SIR?", "sir?")
                        full_response   += token
                        sentence_buffer += token
                        yield token
                        sentences = re.split(r'(?<=[.!?])\s+', sentence_buffer)
                        if len(sentences) > 1:
                            for s in sentences[:-1]:
                                s = s.strip()
                                if s:
                                    queue_sentence(s, loop)
                            sentence_buffer = sentences[-1]
                        if d.get("done"):
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue
    except Exception as e:
        print(f"[JARVIS] Ollama stream error: {e}")
        yield "Apologies, sir. Connection to the local model failed."
        return

    print(f"[JARVIS] Ollama response: {len(full_response)} chars")
    if sentence_buffer.strip():
        queue_sentence(sentence_buffer.strip(), loop)
    if full_response.strip():
        await save_exchange(user_message, full_response)

# ── Speak with events ────────────────────────────────────────────────
def speak_with_events(text: str, loop: asyncio.AbstractEventLoop):
    sentences = split_sentences(text)
    for sentence in sentences:
        queue_sentence(sentence, loop)

# ── Voice pipeline ───────────────────────────────────────────────────
def _voice_thread(loop: asyncio.AbstractEventLoop):
    """Batch STT pipeline — record → transcribe → LLM → TTS, sequential."""
    import traceback
    time.sleep(3)
    print("[JARVIS] Voice pipeline ready — speak anytime")

    while True:
        try:
            asyncio.run_coroutine_threadsafe(broadcast("voice:listening"), loop)
            audio = record_command()
            asyncio.run_coroutine_threadsafe(broadcast("voice:processing"), loop)
            text  = transcribe(audio).strip()

            if not text or len(text) < 3:
                continue
            lower = text.lower()
            if lower in ["hey jarvis", "hey, jarvis", "jarvis", "hey", "thank you", "thanks"]:
                continue

            print(f"[JARVIS] Voice command: {text}")
            asyncio.run_coroutine_threadsafe(broadcast(f"voice:transcript:{text}"), loop)

            async def _run(t=text):
                full = ""
                async for token in stream_ollama(t):
                    full += token
                print(f"[JARVIS] Response ({len(full)} chars): {full[:80]}")
                await broadcast(f"voice:response:{full}")

            asyncio.run_coroutine_threadsafe(_run(), loop).result(timeout=60)

        except Exception as e:
            print(f"[JARVIS] Voice error: {e}")
            traceback.print_exc()
            time.sleep(2)


async def voice_pipeline():
    """Async wrapper — launches voice thread with access to event loop."""
    loop = asyncio.get_event_loop()
    threading.Thread(target=_voice_thread, args=(loop,), daemon=True).start()

# ── Startup ──────────────────────────────────────────────────────────
_voice_task = None

@app.on_event("startup")
async def startup():
    global _voice_task
    await init_db()
    print("[JARVIS] Memory database initialized.")
    _voice_task = asyncio.create_task(voice_pipeline())
    await world_state.start()
    register_all_sensors(world_state)
    await scheduler.start(world_state, None, broadcast)
    _voice_task.add_done_callback(
        lambda t: print(f"[JARVIS] Voice task ended: {t.exception() if not t.cancelled() else 'cancelled'}")
    )

# ── WebSocket ────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    for old_ws in list(ws_clients):
        try:
            await old_ws.close()
        except Exception:
            pass
    ws_clients.clear()
    ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in ws_clients:
            ws_clients.remove(websocket)

# ── Routes ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    stats = await get_stats()
    return {"status": "online", "model": MODEL, "memory": stats}

@app.get("/greeting")
async def greeting():
    hour    = datetime.now().hour
    weather = await fetch_cairo_weather()
    text    = get_greeting_text(hour, weather)
    return {"greeting": text}

@app.get("/weather")
async def weather_endpoint():
    """Expose live Cairo weather for the HUD panel."""
    weather = await fetch_cairo_weather()
    if weather:
        return weather
    return {"error": "Weather unavailable"}

@app.post("/chat")
async def chat(message: Message):
    return StreamingResponse(
        stream_ollama(message.content),
        media_type="text/plain"
    )

@app.post("/speak")
async def speak_endpoint(request: SpeakRequest):
    loop = asyncio.get_event_loop()
    speak_with_events(request.text, loop)
    return {"status": "speaking"}


def time_ago(dt_str: str) -> str:
    """Convert ISO timestamp to human-readable time ago string."""
    try:
        dt    = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.utcnow() - dt
        s     = int(delta.total_seconds())
        if s < 60:       return f"{s}s ago"
        if s < 3600:     return f"{s//60}m ago"
        if s < 86400:    return f"{s//3600}h ago"
        if s < 604800:   return f"{s//86400}d ago"
        return dt.strftime("%-d %b").upper()
    except Exception:
        return "—"


@app.get("/github")
async def github_repos():
    """Fetch AGENT17-tech repos + commit activity for top 4 recently pushed."""
    GITHUB_USER = "AGENT17-tech"
    headers     = {"Accept": "application/vnd.github+json", "User-Agent": "JARVIS-Core"}

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r    = await client.get(
                f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=20&sort=pushed",
                headers=headers
            )
            data = r.json()

        if not isinstance(data, list):
            return []

        repos = []
        for r in data[:8]:
            pushed_raw = r.get("pushed_at", "")
            pushed_ago = time_ago(pushed_raw)

            repo_entry = {
                "name":        r.get("name", ""),
                "description": (r.get("description") or "")[:60],
                "language":    r.get("language") or "",
                "stars":       r.get("stargazers_count", 0),
                "forks":       r.get("forks_count", 0),
                "issues":      r.get("open_issues_count", 0),
                "pushed":      pushed_ago,
                "pushed_raw":  pushed_raw,
                "url":         r.get("html_url", ""),
                "commits":     [],
                "sparkline":   [0] * 7,
            }
            repos.append(repo_entry)

        async with httpx.AsyncClient(timeout=12.0) as client:
            for repo in repos[:4]:
                try:
                    since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
                    cr    = await client.get(
                        f"https://api.github.com/repos/{GITHUB_USER}/{repo['name']}/commits?per_page=15&since={since}",
                        headers=headers
                    )
                    commits_raw = cr.json()
                    if not isinstance(commits_raw, list):
                        continue

                    spark   = [0] * 7
                    now_utc = datetime.utcnow()
                    commits_out = []

                    for c in commits_raw:
                        commit_dt_str = c.get("commit", {}).get("author", {}).get("date", "")
                        msg           = c.get("commit", {}).get("message", "").split("\n")[0][:60]
                        author        = c.get("commit", {}).get("author", {}).get("name", "")
                        sha           = c.get("sha", "")[:7]

                        if commit_dt_str:
                            try:
                                cdt      = datetime.strptime(commit_dt_str, "%Y-%m-%dT%H:%M:%SZ")
                                days_ago = (now_utc - cdt).days
                                if 0 <= days_ago < 7:
                                    spark[6 - days_ago] += 1
                                commits_out.append({
                                    "sha":     sha,
                                    "message": msg,
                                    "author":  author,
                                    "time":    time_ago(commit_dt_str),
                                })
                            except Exception:
                                pass

                    repo["commits"]   = commits_out[:5]
                    repo["sparkline"] = spark

                except Exception as ce:
                    print(f"[JARVIS] Commit fetch failed for {repo['name']}: {ce}")
                    continue

        return repos

    except Exception as e:
        print(f"[JARVIS] GitHub fetch failed: {e}")
        return []


# ── Vision endpoints ─────────────────────────────────────────────────
class VisionPromptPayload(BaseModel):
    prompt: str = "Describe what is on the screen concisely."
    monitor: int = 0

class ImageAnalysePayload(BaseModel):
    path:   str
    prompt: str = "Describe this image in detail."

@app.post("/vision/screen")
async def vision_screen(payload: VisionPromptPayload):
    result = await analyse_screen(payload.prompt, payload.monitor)
    return result

@app.post("/vision/image")
async def vision_image(payload: ImageAnalysePayload):
    description = await analyse_image(payload.path, payload.prompt)
    return {"description": description, "path": payload.path}

@app.get("/vision/context")
async def vision_context():
    desc = await get_vision_context()
    return {"context": desc}


@app.post("/shutdown")
async def shutdown_sequence():
    farewell = "Powering down, sir."
    loop = asyncio.get_event_loop()
    threading.Thread(target=speak_with_events, args=(farewell, loop), daemon=True).start()
    return {"status": "shutting down"}

@app.delete("/memory")
async def clear_memory_endpoint():
    await clear_history()
    return {"status": "memory cleared — entities preserved"}

@app.get("/memory/stats")
async def memory_stats():
    return await get_stats()

@app.get("/memory/entities")
async def memory_entities():
    return await get_entities()

class EntityPayload(BaseModel):
    key:   str
    value: str

@app.post("/memory/entity")
async def memory_set_entity(payload: EntityPayload):
    await set_entity(payload.key, payload.value)
    return {"status": "entity saved", "key": payload.key, "value": payload.value}
