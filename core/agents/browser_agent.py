"""
agents/browser_agent.py — Browser Agent
Navigate, scrape, and interact with web pages via Playwright.
"""

import httpx
import asyncio

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "llama3.1:8b"
OPTIONS    = {"num_predict": 400, "temperature": 0.3, "num_gpu": 99}

SYSTEM = """You are JARVIS's browser agent.
You receive scraped web page content and answer questions about it.
Be concise and precise."""


class BrowserAgent:
    async def run(self, message: str, context: list = None) -> str:
        print(f"[BROWSER AGENT] Task: {message[:60]}")

        # Extract URL if present
        import re
        urls = re.findall(
            r'https?://[^\s]+|www\.[^\s]+', message)

        page_content = ""
        if urls:
            page_content = await self._fetch_page(urls[0])

        if page_content:
            prompt = (f"Page content:\n{page_content[:3000]}\n\n"
                      f"User request: {message}")
        else:
            prompt = message

        messages = [{"role": "system", "content": SYSTEM}]
        if context:
            messages += [m for m in context if m.get("content", "").strip()]
        messages.append({"role": "user", "content": prompt})

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
            return f"Browser agent error: {e}"

    async def _fetch_page(self, url: str) -> str:
        """Fetch and extract text from a web page."""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page    = await browser.new_page()
                await page.goto(url, timeout=15000)
                await page.wait_for_load_state("networkidle", timeout=8000)
                content = await page.inner_text("body")
                await browser.close()
                return content[:3000]
        except Exception as e:
            print(f"[BROWSER AGENT] Fetch error: {e}")
            return ""
