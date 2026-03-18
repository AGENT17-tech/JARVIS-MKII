"""
agent_router.py — JARVIS MKIII Agent Router
Routes tasks to specialist agents based on intent detection.
JARVIS commands — agents execute.

Usage:
    from agent_router import router
    result = await router.route("Research transformer attention")
"""

import asyncio
import re
from typing import Optional


# ── Intent patterns ───────────────────────────────────────────────────
INTENT_PATTERNS = {
    "search": [
        "search", "find", "look up", "what is", "who is", "latest",
        "news", "recent", "current", "today", "research", "tell me about",
        "what happened", "when did", "how many", "price of",
    ],
    "code": [
        "write code", "fix", "debug", "function", "script", "program",
        "error", "bug", "implement", "class", "def ", "import",
        "python", "javascript", "c++", "compile", "syntax", "algorithm",
        "refactor", "optimize", "explain this code",
    ],
    "file": [
        "read file", "open file", "summarise file", "what's in",
        "list files", "create file", "write to file", "save",
        "document", "txt", "pdf", "folder", "directory",
    ],
    "browser": [
        "open", "go to", "navigate", "website", "url", "browse",
        "click", "fill", "scrape", "download", "buc", "portal",
        "gmail", "youtube", "google",
    ],
    "memory": [
        "remember", "what did i", "last time", "previously",
        "history", "recall", "forget", "note that", "keep in mind",
    ],
}


def detect_intent(message: str) -> list:
    """Detect which agents are needed for a message."""
    msg_lower  = message.lower()
    intents    = []

    for intent, patterns in INTENT_PATTERNS.items():
        if any(p in msg_lower for p in patterns):
            intents.append(intent)

    # Default to search for complex questions with no clear intent
    if not intents and len(message.split()) > 5:
        intents = ["search"]

    return intents or ["default"]



# ── Query complexity tiers ────────────────────────────────────────────
SIMPLE_PATTERNS = [
    "hello", "hi", "hey", "what time", "who are you",
    "thanks", "thank you", "ok", "okay", "yes", "no", "good morning",
    "good night", "how are you", "what is your name",
]

KNOWLEDGE_PATTERNS = [
    "what is", "what are", "what was", "what were", "who is", "who was",
    "how does", "how do", "tell me about", "explain what", "define",
    "meaning of", "what does", "describe",
]

KNOWLEDGE_PATTERNS = [
    "what is", "what are", "what was", "what were", "who is", "who was",
    "how does", "how do", "tell me about", "explain what", "define",
    "meaning of", "what does", "describe",
]

COMPLEX_PATTERNS = [
    "explain", "analyse", "analyze", "compare", "research", "write",
    "summarise", "summarize", "design", "implement", "architecture",
    "difference between", "how does", "why does", "what are the",
    "pros and cons", "step by step", "in detail", "comprehensive",
]

def classify_complexity(message: str) -> str:
    """Returns: simple | medium | complex"""
    msg_lower = message.lower()
    if any(p in msg_lower for p in COMPLEX_PATTERNS) or len(message.split()) > 20:
        return "complex"
    if any(p in msg_lower for p in KNOWLEDGE_PATTERNS):
        return "medium"
    if any(p in msg_lower for p in SIMPLE_PATTERNS) and len(message.split()) < 6:
        return "simple"
    return "medium"

MODEL_TIER = {
    "simple":  "qwen3:1.7b",
    "medium":  "llama3.2:3b",
    "complex": "llama3.1:8b",
}

class AgentRouter:
    def __init__(self):
        self._agents = {}
        print("[ROUTER] Agent router initialized.")

    def register(self, name: str, agent):
        self._agents[name] = agent
        print(f"[ROUTER] Agent registered: {name}")

    async def route(self, message: str, context: list = None) -> str:
        """
        Route a message to the appropriate agent(s).
        Returns synthesised response.
        """
        intents = detect_intent(message)
        complexity = classify_complexity(message)
        tier_model = MODEL_TIER[complexity]
        print(f"[ROUTER] Message: '{message[:60]}' → intents: {intents} | tier: {complexity} ({tier_model})")

        # Single intent — direct route
        if len(intents) == 1:
            agent_name = intents[0]
            agent = self._agents.get(agent_name) or self._agents.get("default")
            if agent:
                if agent_name == "default" and hasattr(agent, "run"):
                    return await agent.run(message, context or [], model=tier_model)
                return await agent.run(message, context or [])

        # Multiple intents — parallel execution
        tasks   = []
        names   = []
        for intent in intents:
            agent = self._agents.get(intent)
            if agent:
                tasks.append(agent.run(message, context or []))
                names.append(intent)

        if not tasks:
            agent = self._agents.get("default")
            if agent:
                return await agent.run(message, context or [])
            return "No agent available for this request, sir."

        results  = await asyncio.gather(*tasks, return_exceptions=True)
        combined = []
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                print(f"[ROUTER] Agent {name} failed: {result}")
            elif result and isinstance(result, str):
                combined.append(result.strip())

        if not combined:
            return "All agents failed to respond, sir."

        # If single result, return directly
        if len(combined) == 1:
            return combined[0]

        # Synthesise multiple results
        synth_agent = self._agents.get("default")
        if synth_agent:
            synthesis_prompt = (
                f"Synthesise these agent responses into one concise answer:\n\n"
                + "\n\n---\n\n".join(combined)
            )
            return await synth_agent.run(synthesis_prompt, [])

        return "\n\n".join(combined)


# ── Singleton ─────────────────────────────────────────────────────────
router = AgentRouter()
