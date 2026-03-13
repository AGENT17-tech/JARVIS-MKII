"""
JARVIS Vision Module
────────────────────
Screen capture + image analysis via moondream (Ollama).
Provides:
  - take_screenshot()       → captures screen, returns base64 + saves file
  - analyse_screen(prompt)  → screenshot → moondream → text description
  - analyse_image(path, prompt) → analyse any image file
  - get_vision_context()    → concise screen summary for JARVIS context injection
"""

import mss
import mss.tools
import base64
import httpx
import asyncio
import os
import time
from PIL import Image
from io import BytesIO
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/generate"
VISION_MODEL    = "moondream"
SCREENSHOT_DIR  = Path.home() / "jarvis-core" / "screenshots"
MAX_STORED      = 10          # keep last N screenshots on disk
JPEG_QUALITY    = 82          # balance quality vs token size
MAX_WIDTH       = 1280        # downscale if wider — moondream works fine at 1280px

# Default prompts
SCREEN_PROMPT   = "Describe what is on the screen concisely. Focus on: app name, main content visible, any text, what the user appears to be doing."
CONTEXT_PROMPT  = "In one sentence, what is the user currently doing on their screen?"

# ── Setup ─────────────────────────────────────────────────────────────────────
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _resize_if_needed(img: Image.Image) -> Image.Image:
    """Downscale wide screenshots to MAX_WIDTH — preserves aspect ratio."""
    if img.width > MAX_WIDTH:
        ratio  = MAX_WIDTH / img.width
        new_h  = int(img.height * ratio)
        img    = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)
    return img


def _cleanup_old_screenshots():
    """Keep only the last MAX_STORED screenshots on disk."""
    files = sorted(SCREENSHOT_DIR.glob("screen_*.jpg"), key=os.path.getmtime)
    for f in files[:-MAX_STORED]:
        try:
            f.unlink()
        except Exception:
            pass


def take_screenshot(monitor: int = 0) -> dict:
    """
    Capture the screen.
    monitor=0 → all monitors combined, 1/2/3 → specific monitor.
    Returns: { "path": str, "base64": str, "width": int, "height": int }
    """
    with mss.mss() as sct:
        mon    = sct.monitors[monitor]
        raw    = sct.grab(mon)
        img    = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    img  = _resize_if_needed(img)

    # Save to disk
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path      = SCREENSHOT_DIR / f"screen_{timestamp}.jpg"
    img.save(str(path), "JPEG", quality=JPEG_QUALITY)
    _cleanup_old_screenshots()

    # Encode to base64 for Ollama
    buf = BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "path":   str(path),
        "base64": b64,
        "width":  img.width,
        "height": img.height,
    }


def image_to_base64(image_path: str) -> str:
    """Load any image file and return base64 string."""
    with Image.open(image_path) as img:
        img  = img.convert("RGB")
        img  = _resize_if_needed(img)
        buf  = BytesIO()
        img.save(buf, "JPEG", quality=JPEG_QUALITY)
        return base64.b64encode(buf.getvalue()).decode("utf-8")


async def _query_moondream(b64_image: str, prompt: str) -> str:
    """Send image + prompt to moondream via Ollama generate endpoint."""
    payload = {
        "model":  VISION_MODEL,
        "prompt": prompt,
        "images": [b64_image],
        "stream": False,
        "options": {
            "num_predict": 200,
            "temperature": 0.2,   # low temp — factual description
        }
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r    = await client.post(OLLAMA_URL, json=payload)
            data = r.json()
            return data.get("response", "").strip()
    except Exception as e:
        print(f"[JARVIS Vision] moondream query failed: {e}")
        return ""


async def analyse_screen(prompt: str = SCREEN_PROMPT, monitor: int = 0) -> dict:
    """
    Capture screen and analyse it.
    Returns: { "description": str, "screenshot_path": str, "width": int, "height": int }
    """
    try:
        shot = take_screenshot(monitor)
        desc = await _query_moondream(shot["base64"], prompt)
        return {
            "description":     desc,
            "screenshot_path": shot["path"],
            "width":           shot["width"],
            "height":          shot["height"],
        }
    except Exception as e:
        print(f"[JARVIS Vision] analyse_screen failed: {e}")
        return {"description": "Vision analysis unavailable.", "screenshot_path": "", "width": 0, "height": 0}


async def analyse_image(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """Analyse any image file with moondream."""
    try:
        b64  = image_to_base64(image_path)
        return await _query_moondream(b64, prompt)
    except Exception as e:
        print(f"[JARVIS Vision] analyse_image failed: {e}")
        return "Could not analyse image."


async def get_vision_context() -> str:
    """
    One-sentence screen summary — injected into JARVIS context so it knows
    what the user is looking at without being asked.
    Returns empty string if vision is slow or fails (non-blocking).
    """
    try:
        result = await asyncio.wait_for(
            analyse_screen(CONTEXT_PROMPT),
            timeout=8.0   # don't block chat for more than 8s
        )
        return result.get("description", "")
    except asyncio.TimeoutError:
        print("[JARVIS Vision] context timeout — skipping vision injection")
        return ""
    except Exception as e:
        print(f"[JARVIS Vision] get_vision_context failed: {e}")
        return ""


# ── Sync wrapper for non-async callers ───────────────────────────────────────
def analyse_screen_sync(prompt: str = SCREEN_PROMPT) -> dict:
    """Synchronous wrapper — use when calling from non-async context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(analyse_screen(prompt))
    finally:
        loop.close()
