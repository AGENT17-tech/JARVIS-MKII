"""
agents/file_agent.py — File Agent
Read, write, and summarise files using sandbox + qwen3:1.7b.
"""

import httpx
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sandbox import sandbox

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:1.7b"
OPTIONS    = {"num_predict": 500, "temperature": 0.3, "num_gpu": 99}

SYSTEM = """You are JARVIS's file agent.
Summarise documents precisely. Extract key information.
Be concise — bullet points for long documents."""


class FileAgent:
    async def run(self, message: str, context: list = None) -> str:
        print(f"[FILE AGENT] Task: {message[:60]}")

        # Try to extract a file path from the message
        file_content = ""
        import re
        paths = re.findall(r'[~/][\w/._-]+\.\w+', message)
        for path in paths:
            result = sandbox.execute("file_read", path=path)
            if result.get("ok"):
                file_content = result["result"][:3000]
                break

        if file_content:
            prompt = f"File contents:\n{file_content}\n\nUser request: {message}"
        else:
            prompt = message

        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages += [m for m in context if m.get("content", "").strip()]
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(OLLAMA_URL, json={
                    "model":    MODEL,
                    "messages": messages,
                    "stream":   False,
                    "options":  OPTIONS,
                })
                return r.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"File agent error: {e}"
