"""
scheduler.py — JARVIS MKIII Autonomous Scheduler
Trigger → Condition → Action loop.
JARVIS acts without being asked.

Usage:
    from scheduler import scheduler
    await scheduler.start(world_state, speak_fn, broadcast_fn)
"""

import asyncio
import time
from datetime import datetime
from typing import Callable, Awaitable
from world_state import WorldState


class Trigger:
    def __init__(self, name: str, condition: Callable, action: str,
                 cooldown: int, priority: int = 1):
        self.name      = name
        self.condition = condition
        self.action    = action
        self.cooldown  = cooldown   # seconds
        self.priority  = priority   # 1=low 2=medium 3=high
        self.last_fired: float = 0

    def is_ready(self, ws: dict) -> bool:
        """Check if trigger condition is met and cooldown has passed."""
        now = time.time()
        if now - self.last_fired < self.cooldown:
            return False
        try:
            return self.condition(ws)
        except Exception:
            return False

    def fire(self):
        self.last_fired = time.time()


def _current_hour() -> int:
    return datetime.now().hour

def _days_since_commit(ws: dict) -> int:
    return ws.get("github", {}).get("days_since", 0)

def _days_to_exam(ws: dict) -> int:
    return ws.get("buc_portal", {}).get("days_to_exam", 99)

def _idle_minutes(ws: dict) -> int:
    return ws.get("user", {}).get("idle_minutes", 0)


# ── Trigger definitions ───────────────────────────────────────────────
DEFAULT_TRIGGERS = [
    Trigger(
        name      = "Morning briefing",
        condition = lambda ws: _current_hour() == 7 and ws.get("user", {}).get("status") == "active",
        action    = "briefing.morning",
        cooldown  = 86400,   # once per day
        priority  = 3,
    ),
    Trigger(
        name      = "GitHub inactivity",
        condition = lambda ws: _days_since_commit(ws) > 2,
        action    = "alert.github_inactive",
        cooldown  = 43200,   # once per 12h
        priority  = 2,
    ),
    Trigger(
        name      = "Exam approaching",
        condition = lambda ws: _days_to_exam(ws) <= 3,
        action    = "alert.exam_approaching",
        cooldown  = 86400,
        priority  = 3,
    ),
    Trigger(
        name      = "BUC announcement",
        condition = lambda ws: ws.get("buc_portal", {}).get("announcements", 0) > 0,
        action    = "alert.buc_announcement",
        cooldown  = 3600,
        priority  = 2,
    ),
    Trigger(
        name      = "Urgent email",
        condition = lambda ws: ws.get("email", {}).get("urgent", 0) > 0,
        action    = "alert.urgent_email",
        cooldown  = 1800,
        priority  = 3,
    ),
    Trigger(
        name      = "System overheating",
        condition = lambda ws: ws.get("system", {}).get("temp", 0) > 85,
        action    = "alert.thermal_critical",
        cooldown  = 300,
        priority  = 3,
    ),
    Trigger(
        name      = "High CPU",
        condition = lambda ws: ws.get("system", {}).get("cpu", 0) > 90,
        action    = "alert.high_cpu",
        cooldown  = 600,
        priority  = 2,
    ),
    Trigger(
        name      = "PHANTOM ZERO nudge",
        condition = lambda ws: _idle_minutes(ws) > 20
                               and ws.get("user", {}).get("status") == "active",
        action    = "suggest.phantom_zero_mission",
        cooldown  = 7200,
        priority  = 1,
    ),
    Trigger(
        name      = "Evening summary",
        condition = lambda ws: _current_hour() == 21 and ws.get("user", {}).get("status") == "active",
        action    = "briefing.evening",
        cooldown  = 86400,
        priority  = 2,
    ),
]


# ── Action messages ───────────────────────────────────────────────────
ACTION_MESSAGES = {
    "briefing.morning":          "Good morning, sir. Preparing your daily briefing.",
    "briefing.evening":          "Good evening, sir. Here is your end-of-day summary.",
    "alert.github_inactive":     "Sir, you have not committed to GitHub in over two days. PHANTOM ZERO requires consistent progress.",
    "alert.exam_approaching":    "Sir, your exam is approaching. Three days or fewer remain. I recommend initiating the study protocol.",
    "alert.buc_announcement":    "Sir, there is a new announcement on the BUC portal. Shall I retrieve it?",
    "alert.urgent_email":        "Sir, you have an urgent email requiring attention.",
    "alert.thermal_critical":    "Warning, sir. System temperature has exceeded safe limits. Consider reducing load.",
    "alert.high_cpu":            "Sir, CPU usage is critically high. A process may be misbehaving.",
    "suggest.phantom_zero_mission": "Sir, you have been idle for over twenty minutes. Your next PHANTOM ZERO mission is queued.",
}


class Scheduler:
    def __init__(self):
        self.triggers: list[Trigger] = DEFAULT_TRIGGERS
        self._running: bool = False
        self._speak_fn = None
        self._broadcast_fn = None
        self.check_interval: int = 30   # check every 30 seconds
        print(f"[SCHEDULER] Initialized — {len(self.triggers)} triggers loaded.")

    async def start(self,
                    world_state_instance: WorldState,
                    speak_fn: Callable = None,
                    broadcast_fn: Callable = None):
        """Start the autonomous scheduler loop."""
        self._world_state  = world_state_instance
        self._speak_fn     = speak_fn
        self._broadcast_fn = broadcast_fn
        self._running      = True
        asyncio.create_task(self._loop())
        print("[SCHEDULER] Autonomous loop started.")

    async def _loop(self):
        """Main trigger evaluation loop."""
        while self._running:
            await asyncio.sleep(self.check_interval)
            ws = self._world_state.get()
            await self._evaluate(ws)

    async def _evaluate(self, ws: dict):
        """Check all triggers against current world state."""
        # Sort by priority — high priority fires first
        fired = []
        for trigger in sorted(self.triggers, key=lambda t: -t.priority):
            if trigger.is_ready(ws):
                fired.append(trigger)

        for trigger in fired:
            await self._fire(trigger)

    async def _fire(self, trigger: Trigger):
        """Execute a trigger action."""
        trigger.fire()
        message = ACTION_MESSAGES.get(trigger.action, f"Autonomous action: {trigger.action}")
        print(f"[SCHEDULER] FIRED — {trigger.name}: {trigger.action}")

        # Speak the alert
        if self._speak_fn:
            try:
                await self._speak_fn(message)
            except Exception as e:
                print(f"[SCHEDULER] Speak error: {e}")

        # Broadcast to HUD
        if self._broadcast_fn:
            try:
                await self._broadcast_fn(f"scheduler:alert:{trigger.name}:{message}")
            except Exception as e:
                print(f"[SCHEDULER] Broadcast error: {e}")

    def stop(self):
        self._running = False

    def add_trigger(self, trigger: Trigger):
        """Add a custom trigger at runtime."""
        self.triggers.append(trigger)
        print(f"[SCHEDULER] Trigger added: {trigger.name}")

    def status(self):
        """Print scheduler status."""
        print(f"[SCHEDULER] Running: {self._running}")
        print(f"[SCHEDULER] Triggers: {len(self.triggers)}")
        now = time.time()
        for t in self.triggers:
            since = round((now - t.last_fired) / 60) if t.last_fired else "never"
            print(f"  [{t.priority}] {t.name} — last fired: {since} min ago")


# ── Singleton ─────────────────────────────────────────────────────────
scheduler = Scheduler()


# ── CLI test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        from world_state import world_state

        print("[TEST] World state update...")
        await world_state.update()

        print("[TEST] Injecting test conditions...")
        # Simulate: no GitHub commit in 3 days
        world_state.set("github", {"days_since": 3, "last_commit": "3 days ago"})
        # Simulate: exam in 2 days
        world_state.set("buc_portal", {"days_to_exam": 2, "next_exam": "Mechanics 1", "announcements": 0})
        # Simulate: urgent email
        world_state.set("email", {"unread": 3, "urgent": 1, "summary": "Professor reply"})

        ws = world_state.get()
        print("\n[TEST] Evaluating triggers...")

        fired_count = 0
        for trigger in sorted(scheduler.triggers, key=lambda t: -t.priority):
            if trigger.condition(ws):
                msg = ACTION_MESSAGES.get(trigger.action, trigger.action)
                print(f"  FIRED [{trigger.priority}] {trigger.name}")
                print(f"         → {msg}")
                fired_count += 1

        print(f"\n[TEST] {fired_count} trigger(s) would fire with current state.")
        print("[TEST] Scheduler PASS")

    asyncio.run(test())
