"""
agents/memory_agent.py — Memory Agent
Entity extraction, context compression, and memory recall.
"""

import httpx
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "qwen3:1.7b"
OPTIONS    = {"num_predict": 300, "temperature": 0.3, "num_gpu": 99}

SYSTEM = """You are JARVIS's memory agent.
Extract key facts, entities, and important information from conversations.
Format as concise bullet points. Focus on: names, dates, decisions, preferences."""


class MemoryAgent:
    async def run(self, message: str, context: list = None) -> str:
        print(f"[MEMORY AGENT] Task: {message[:60]}")

        # Pull from Hindsight memory
        memory_context = ""
        try:
            import sys
            sys.path.insert(0, os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))
            from memory import recall
            memories = await recall(message, limit=5)
            if memories:
                memory_context = "\n".join(
                    m.get("content", "")[:100] for m in memories)
        except Exception:
            pass

        prompt = message
        if memory_context:
            prompt = f"Relevant memories:\n{memory_context}\n\nRequest: {message}"

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
            return f"Memory agent error: {e}"
