"""
agents/default_agent.py — Default Agent
Fast responses using qwen3:1.7b for simple Q&A and synthesis.
"""

import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:1.7b"
OPTIONS    = {"num_predict": 300, "temperature": 0.7, "num_gpu": 99}

SYSTEM = """You are JARVIS — Just A Rather Very Intelligent System.
Built by Khalid Walid — polymath engineer, Tony Stark's successor.
Be precise, composed, and brief. Address the user as 'sir'. No fluff."""


class DefaultAgent:
    async def run(self, message: str, context: list = None) -> str:
        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages += [m for m in context if m.get("content", "").strip()]
        messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(OLLAMA_URL, json={
                    "model":    MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  OPTIONS,
                })
                data    = r.json()
                content = data.get("message", {}).get("content", "")
                content = content.replace("SIR", "sir").replace("Sir", "sir")
                return content
        except Exception as e:
            return f"Default agent error, sir: {e}"
