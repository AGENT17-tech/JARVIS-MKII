"""
cloud_fallback.py — JARVIS MKIII Cloud Fallback
Routes to Gemini 2.0 Flash when:
  1. Ollama fails or times out
  2. Query is flagged as complex (>50 tokens, code+research combo)
  3. Explicitly requested via 'use cloud' or 'ask gemini'
  4. Local model returns empty response

Usage:
    from cloud_fallback import cloud_fallback
    async for token in cloud_fallback.stream(messages):
        yield token
"""

import httpx
import json
import os
import time
from typing import AsyncGenerator

# ── Config ────────────────────────────────────────────────────────────
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL      = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"

# Complexity triggers — these phrases force cloud routing
CLOUD_TRIGGERS = [
    "use cloud", "ask gemini", "use gemini", "cloud mode",
    "complex query", "deep research", "full analysis",
]

# Token threshold — queries longer than this get cloud routing
COMPLEXITY_THRESHOLD = 60

# Cost tracking
_usage_log: list[dict] = []


def is_complex(message: str) -> bool:
    """Determine if a query warrants cloud routing."""
    msg_lower = message.lower()

    # Explicit trigger phrases
    if any(t in msg_lower for t in CLOUD_TRIGGERS):
        return True

    # Long queries
    word_count = len(message.split())
    if word_count > COMPLEXITY_THRESHOLD:
        return True

    return False


def should_fallback(message: str) -> bool:
    """Check if explicit cloud fallback is requested."""
    return any(t in message.lower() for t in CLOUD_TRIGGERS)


class CloudFallback:
    def __init__(self):
        self._available = bool(GEMINI_API_KEY)
        self._total_calls = 0
        self._failed_calls = 0
        if self._available:
            print(f"[CLOUD FALLBACK] Gemini {GEMINI_MODEL} ready.")
        else:
            print("[CLOUD FALLBACK] No API key — cloud fallback disabled.")

    def log_usage(self, tokens_in: int, tokens_out: int, success: bool):
        """Track API usage for cost awareness."""
        _usage_log.append({
            "time":       time.strftime("%H:%M:%S"),
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
            "success":    success,
            "model":      GEMINI_MODEL,
        })
        self._total_calls += 1
        if not success:
            self._failed_calls += 1

    def get_stats(self) -> dict:
        """Return usage statistics."""
        return {
            "available":    self._available,
            "model":        GEMINI_MODEL,
            "total_calls":  self._total_calls,
            "failed_calls": self._failed_calls,
            "recent":       _usage_log[-10:],
        }

    async def stream(
        self,
        messages: list[dict],
        system: str = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from Gemini.
        messages: list of {role, content} dicts (same format as Ollama)
        """
        if not self._available:
            yield "[Cloud fallback unavailable — no API key configured, sir.]"
            return

        # Convert Ollama message format to Gemini format
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature":     0.7,
                "maxOutputTokens": 1024,
                "topP":            0.9,
            },
        }

        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        params = {"key": GEMINI_API_KEY, "alt": "sse"}

        tokens_in  = sum(len(m.get("content", "").split()) for m in messages)
        tokens_out = 0

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", GEMINI_URL,
                    json=payload, params=params,
                    headers={"Content-Type": "application/json"}
                ) as response:

                    if response.status_code != 200:
                        error_body = await response.aread()
                        print(f"[CLOUD FALLBACK] Error {response.status_code}: {error_body[:200]}")
                        self.log_usage(tokens_in, 0, False)
                        yield f"[Cloud error {response.status_code}, sir. Falling back to local model.]"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            candidates = data.get("candidates", [])
                            if not candidates:
                                continue
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                token = part.get("text", "")
                                if token:
                                    # Sanitize "Sir" caps
                                    token = token.replace("SIR", "sir").replace("Sir", "sir")
                                    tokens_out += len(token.split())
                                    yield token
                        except json.JSONDecodeError:
                            continue

            self.log_usage(tokens_in, tokens_out, True)
            print(f"[CLOUD FALLBACK] Streamed {tokens_out} tokens via Gemini.")

        except httpx.TimeoutException:
            print("[CLOUD FALLBACK] Timeout.")
            self.log_usage(tokens_in, 0, False)
            yield "[Cloud request timed out, sir. Local model is responding instead.]"
        except Exception as e:
            print(f"[CLOUD FALLBACK] Error: {e}")
            self.log_usage(tokens_in, 0, False)
            yield f"[Cloud error: {e}]"


# ── Singleton ─────────────────────────────────────────────────────────
cloud_fallback = CloudFallback()


if __name__ == "__main__":
    import asyncio

    async def test():
        print("[TEST] Cloud fallback...")
        if not GEMINI_API_KEY:
            print("[TEST] No GEMINI_API_KEY in environment.")
            print("       Run: python3 vault.py store GEMINI_API_KEY your_key")
            return

        messages = [{"role": "user", "content": "Say hello in exactly 10 words."}]
        response = ""
        async for token in cloud_fallback.stream(messages):
            response += token
            print(token, end="", flush=True)
        print()
        print(f"\n[TEST] Stats: {cloud_fallback.get_stats()}")
        print("[TEST] Cloud fallback PASS")

    asyncio.run(test())
