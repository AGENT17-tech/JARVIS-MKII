"""
world_state.py — JARVIS MKIII World State Engine
Continuously updated JSON representing everything JARVIS knows.
Updates every 60 seconds passively, real-time for critical alerts.

Usage:
    from world_state import world_state
    await world_state.start()
    state = world_state.get()
"""

import asyncio
import psutil
import os
import json
from datetime import datetime
from typing import Any


class WorldState:
    def __init__(self):
        self._state: dict = {}
        self._sensors: list = []
        self._running: bool = False
        self.update_interval: int = 60  # seconds
        self._init_default_state()
        print("[WORLD STATE] Engine initialized.")

    def _init_default_state(self):
        """Set default empty state structure."""
        self._state = {
            "time":         "",
            "user": {
                "status":       "unknown",
                "last_seen":    "",
                "focus_mode":   False,
                "current_task": "",
                "idle_minutes": 0,
            },
            "system": {
                "cpu":      0,
                "ram":      0,
                "gpu_vram": 0,
                "temp":     0,
                "disk_free": "",
            },
            "calendar": {
                "next_event":    "",
                "events_today":  0,
                "deadline_soon": "",
            },
            "email": {
                "unread":  0,
                "urgent":  0,
                "summary": "",
            },
            "github": {
                "last_commit":    "",
                "days_since":     0,
                "open_prs":       0,
                "pending_todos":  [],
            },
            "buc_portal": {
                "grades_updated":  False,
                "announcements":   0,
                "next_exam":       "",
                "days_to_exam":    99,
            },
            "discord": {
                "unread_messages": 0,
                "mentions":        0,
            },
            "threat_level":  "minimal",
            "mood_estimate": "unknown",
            "last_updated":  "",
        }

    # ── Sensor registration ───────────────────────────────────────────
    def register_sensor(self, sensor):
        """Register a sensor that provides state updates."""
        self._sensors.append(sensor)
        print(f"[WORLD STATE] Sensor registered: {sensor.__class__.__name__}")

    # ── System metrics (always available) ────────────────────────────
    def _read_system_metrics(self) -> dict:
        """Read CPU, RAM, disk — no external dependencies."""
        try:
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/")
            disk_free = f"{disk.free // (1024**3)}GB free"

            # Temperature (Linux only)
            temp = 0
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temp = round(entries[0].current)
                            break
            except Exception:
                pass

            # GPU VRAM via nvidia-smi
            gpu_vram = 0
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used,memory.total",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    used, total = result.stdout.strip().split(", ")
                    gpu_vram = round(int(used) / int(total) * 100)
            except Exception:
                pass

            return {
                "cpu":       round(cpu),
                "ram":       round(ram),
                "gpu_vram":  gpu_vram,
                "temp":      temp,
                "disk_free": disk_free,
            }
        except Exception as e:
            print(f"[WORLD STATE] System metrics error: {e}")
            return self._state.get("system", {})

    def _assess_threat_level(self) -> str:
        """Assess overall system threat level."""
        sys = self._state.get("system", {})
        if sys.get("temp", 0) > 85 or sys.get("cpu", 0) > 90:
            return "critical"
        if sys.get("temp", 0) > 75 or sys.get("cpu", 0) > 75:
            return "elevated"
        return "minimal"

    # ── Core update ───────────────────────────────────────────────────
    async def update(self):
        """Pull fresh data from all sensors + system metrics."""
        now = datetime.now()

        # Always update time and system
        self._state["time"]        = now.isoformat()
        self._state["last_updated"] = now.strftime("%H:%M:%S")
        self._state["system"]      = self._read_system_metrics()
        self._state["threat_level"] = self._assess_threat_level()

        # Update user status
        self._state["user"]["last_seen"] = now.strftime("%H:%M")
        self._state["user"]["status"]    = "active"

        # Pull from registered sensors
        for sensor in self._sensors:
            try:
                data = await sensor.read()
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key in self._state:
                            if isinstance(self._state[key], dict) and isinstance(value, dict):
                                self._state[key].update(value)
                            else:
                                self._state[key] = value
            except Exception as e:
                print(f"[WORLD STATE] Sensor error ({sensor.__class__.__name__}): {e}")

        print(f"[WORLD STATE] Updated — CPU:{self._state['system']['cpu']}% "
              f"RAM:{self._state['system']['ram']}% "
              f"Threat:{self._state['threat_level']}")

    async def run(self):
        """Continuous update loop."""
        self._running = True
        print("[WORLD STATE] Loop started.")
        while self._running:
            await self.update()
            await asyncio.sleep(self.update_interval)

    async def start(self):
        """Start the world state loop as a background task."""
        await self.update()   # immediate first update
        asyncio.create_task(self.run())

    def stop(self):
        self._running = False

    # ── Accessors ─────────────────────────────────────────────────────
    def get(self, key: str = None, default: Any = None) -> Any:
        """Get full state or a specific key."""
        if key is None:
            return self._state.copy()
        return self._state.get(key, default)

    def get_nested(self, *keys, default=None) -> Any:
        """Get a nested value. E.g. get_nested('system', 'cpu')"""
        val = self._state
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, default)
            else:
                return default
        return val

    def set(self, key: str, value: Any):
        """Manually override a state value."""
        self._state[key] = value

    def summary(self) -> str:
        """One-line human readable summary for JARVIS briefings."""
        s   = self._state
        sys = s.get("system", {})
        cal = s.get("calendar", {})
        gh  = s.get("github", {})
        buc = s.get("buc_portal", {})

        parts = []
        if sys.get("temp", 0) > 75:
            parts.append(f"System temp {sys['temp']}C")
        if cal.get("next_event"):
            parts.append(f"Next: {cal['next_event']}")
        if gh.get("days_since", 0) > 2:
            parts.append(f"No GitHub commit in {gh['days_since']} days")
        if buc.get("days_to_exam", 99) <= 3:
            parts.append(f"Exam in {buc['days_to_exam']} days")
        if s.get("email", {}).get("urgent", 0) > 0:
            parts.append(f"{s['email']['urgent']} urgent email(s)")

        return " | ".join(parts) if parts else "All clear."

    def to_json(self) -> str:
        return json.dumps(self._state, indent=2, default=str)


# ── Singleton ─────────────────────────────────────────────────────────
world_state = WorldState()


# ── CLI test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        print("[TEST] Starting world state update...")
        await world_state.update()
        state = world_state.get()
        print(f"Time:       {state['time']}")
        print(f"CPU:        {state['system']['cpu']}%")
        print(f"RAM:        {state['system']['ram']}%")
        print(f"GPU VRAM:   {state['system']['gpu_vram']}%")
        print(f"Temp:       {state['system']['temp']}C")
        print(f"Disk:       {state['system']['disk_free']}")
        print(f"Threat:     {state['threat_level']}")
        print(f"Summary:    {world_state.summary()}")
        print("\n[TEST] World state PASS")

    asyncio.run(test())
