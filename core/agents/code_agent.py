"""
agents/code_agent.py — Code Agent
Code generation, debugging, and explanation using llama3.1:8b.
"""

import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "llama3.1:8b"
OPTIONS    = {"num_predict": 800, "temperature": 0.2, "num_gpu": 99}

SYSTEM = """You are JARVIS's code agent — an expert software engineer.
Write clean, working code. Explain bugs precisely. No filler.
Always include comments. Default to Python unless specified."""


class CodeAgent:
    async def run(self, message: str, context: list = None) -> str:
        print(f"[CODE AGENT] Task: {message[:60]}")
        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages += [m for m in context if m.get("content", "").strip()]
        messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(OLLAMA_URL, json={
                    "model":    MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  OPTIONS,
                })
                return r.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"Code agent error: {e}"
