"""
agents/__init__.py — JARVIS MKIII Agent Registry
Initialises and registers all specialist agents with the router.

Usage:
    from agents import register_all_agents
    register_all_agents(router)
"""

from agent_router import AgentRouter


def register_all_agents(router: AgentRouter):
    """Register all specialist agents."""

    try:
        from agents.default_agent import DefaultAgent
        router.register("default", DefaultAgent())
    except Exception as e:
        print(f"[AGENTS] Default agent failed: {e}")

    try:
        from agents.search_agent import SearchAgent
        router.register("search", SearchAgent())
    except Exception as e:
        print(f"[AGENTS] Search agent failed: {e}")

    try:
        from agents.code_agent import CodeAgent
        router.register("code", CodeAgent())
    except Exception as e:
        print(f"[AGENTS] Code agent failed: {e}")

    try:
        from agents.file_agent import FileAgent
        router.register("file", FileAgent())
    except Exception as e:
        print(f"[AGENTS] File agent failed: {e}")

    try:
        from agents.browser_agent import BrowserAgent
        router.register("browser", BrowserAgent())
    except Exception as e:
        print(f"[AGENTS] Browser agent failed: {e}")

    try:
        from agents.memory_agent import MemoryAgent
        router.register("memory", MemoryAgent())
    except Exception as e:
        print(f"[AGENTS] Memory agent failed: {e}")

    print(f"[AGENTS] {len(router._agents)} agent(s) registered.")
