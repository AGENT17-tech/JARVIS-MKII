"""
agents/search_agent.py — Search Agent
Web research using DuckDuckGo + llama3.1:8b for analysis.
No API key required.
"""

import httpx
import asyncio

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "llama3.1:8b"
OPTIONS    = {"num_predict": 500, "temperature": 0.3, "num_gpu": 99}

SYSTEM = """You are JARVIS's research agent.
Your job: search the web, extract key facts, return a concise briefing.
Be precise. No filler. Address results as briefing points."""


async def web_search(query: str, max_results: int = 5) -> list:
    """Search DuckDuckGo — no API key needed."""
    try:
        params = {
            "q":      query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params=params,
                headers={"User-Agent": "JARVIS-MKIII"}
            )
            data    = r.json()
            results = []

            # Abstract
            if data.get("Abstract"):
                results.append({
                    "title":   data.get("Heading", ""),
                    "snippet": data["Abstract"][:300],
                    "url":     data.get("AbstractURL", ""),
                })

            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title":   topic.get("FirstURL", "").split("/")[-1],
                        "snippet": topic["Text"][:200],
                        "url":     topic.get("FirstURL", ""),
                    })

            return results[:max_results]
    except Exception as e:
        print(f"[SEARCH AGENT] Search error: {e}")
        return []


class SearchAgent:
    async def run(self, message: str, context: list = None) -> str:
        print(f"[SEARCH AGENT] Searching: {message[:60]}")

        # Extract search query
        query   = message
        results = await web_search(query)

        if not results:
            # Fall back to LLM knowledge
            return await self._llm_response(message, "", context)

        # Format results for LLM
        results_text = "\n\n".join(
            f"Source: {r.get('url', 'unknown')}\n{r.get('snippet', '')}"
            for r in results
        )

        prompt = (
            f"Based on these search results, answer: {message}\n\n"
            f"Search results:\n{results_text}\n\n"
            f"Provide a concise, accurate briefing."
        )

        return await self._llm_response(prompt, results_text, context)

    async def _llm_response(self, message: str,
                             search_ctx: str, context: list) -> str:
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
            return f"Search agent error: {e}"
