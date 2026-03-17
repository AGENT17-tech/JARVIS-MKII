"""
sandbox.py — JARVIS MKIII Tool Sandbox
Allowlist-based permission system.
No tool accesses what it wasn't explicitly granted.

Usage:
    from sandbox import sandbox
    sandbox.execute("file_read", path="/home/kiko/JARVIS-MKII/core/main.py")
    sandbox.execute("shell", command="ls /home/kiko")
"""

import os
import subprocess
from pathlib import Path

# ── Allowed filesystem paths ──────────────────────────────────────────
ALLOWED_PATHS = [
    os.path.expanduser("~/JARVIS-MKII"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    "/tmp",
]

# ── Allowed shell commands (prefix whitelist) ─────────────────────────
ALLOWED_COMMANDS = [
    "ls", "pwd", "echo", "cat", "mkdir", "cp", "mv", "rm",
    "git", "python3", "pip", "npm", "node",
    "systemctl status", "journalctl",
    "curl", "wget",
    "ollama",
    "docker ps", "docker logs",
]

# ── Blocked patterns (hard deny regardless of allowlist) ─────────────
BLOCKED_PATTERNS = [
    "/etc/passwd", "/etc/shadow", "/etc/sudoers",
    "~/.ssh", ".env", ".key", ".pem", "id_rsa",
    "rm -rf /", "sudo", "chmod 777",
    "/proc/", "/sys/",
]


class Sandbox:
    def __init__(self):
        self.allowed_paths   = [os.path.realpath(p) for p in ALLOWED_PATHS if os.path.exists(p)]
        self.allowed_commands = ALLOWED_COMMANDS
        self.blocked_patterns = BLOCKED_PATTERNS
        print("[SANDBOX] Initialized — tool permissions enforced.")

    # ── Path validation ───────────────────────────────────────────────
    def _is_path_allowed(self, path: str) -> bool:
        real = os.path.realpath(os.path.expanduser(path))
        for allowed in self.allowed_paths:
            if real.startswith(allowed):
                return True
        return False

    def _is_blocked(self, text: str) -> bool:
        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in self.blocked_patterns)

    def _is_command_allowed(self, command: str) -> bool:
        cmd_stripped = command.strip()
        return any(cmd_stripped.startswith(allowed) for allowed in self.allowed_commands)

    # ── Tool execution ────────────────────────────────────────────────
    def execute(self, tool: str, **kwargs) -> dict:
        """
        Execute a sandboxed tool.
        Returns {"ok": True, "result": ...} or {"ok": False, "error": ...}
        """
        # Hard block check on all kwargs values
        for v in kwargs.values():
            if isinstance(v, str) and self._is_blocked(v):
                return self._deny(tool, f"Blocked pattern detected in args: {v}")

        if tool == "file_read":
            return self._file_read(kwargs.get("path", ""))

        elif tool == "file_write":
            return self._file_write(kwargs.get("path", ""), kwargs.get("content", ""))

        elif tool == "file_list":
            return self._file_list(kwargs.get("path", ""))

        elif tool == "shell":
            return self._shell(kwargs.get("command", ""))

        else:
            return self._deny(tool, f"Unknown tool '{tool}' — not in sandbox registry.")

    # ── Tool implementations ──────────────────────────────────────────
    def _file_read(self, path: str) -> dict:
        if not self._is_path_allowed(path):
            return self._deny("file_read", f"Path not in allowlist: {path}")
        try:
            with open(os.path.expanduser(path), "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"ok": True, "result": content}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _file_write(self, path: str, content: str) -> dict:
        if not self._is_path_allowed(path):
            return self._deny("file_write", f"Path not in allowlist: {path}")
        try:
            os.makedirs(os.path.dirname(os.path.expanduser(path)), exist_ok=True)
            with open(os.path.expanduser(path), "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "result": f"Written: {path}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _file_list(self, path: str) -> dict:
        if not self._is_path_allowed(path):
            return self._deny("file_list", f"Path not in allowlist: {path}")
        try:
            entries = os.listdir(os.path.expanduser(path))
            return {"ok": True, "result": entries}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _shell(self, command: str) -> dict:
        if not self._is_command_allowed(command):
            return self._deny("shell", f"Command not in allowlist: {command}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=30
            )
            return {
                "ok":     True,
                "result": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Command timed out (30s limit)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Helpers ───────────────────────────────────────────────────────
    def _deny(self, tool: str, reason: str) -> dict:
        print(f"[SANDBOX] DENIED — {tool}: {reason}")
        return {"ok": False, "error": f"SANDBOX DENIED: {reason}"}

    def add_allowed_path(self, path: str):
        """Dynamically add a trusted path at runtime."""
        real = os.path.realpath(os.path.expanduser(path))
        if real not in self.allowed_paths:
            self.allowed_paths.append(real)
            print(f"[SANDBOX] Path added to allowlist: {real}")

    def status(self):
        print("[SANDBOX] Allowed paths:")
        for p in self.allowed_paths:
            print(f"  + {p}")
        print("[SANDBOX] Allowed commands:")
        for c in self.allowed_commands:
            print(f"  + {c}")


# ── Singleton ─────────────────────────────────────────────────────────
sandbox = Sandbox()


# ── CLI test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== SANDBOX TEST ===\n")

    # Should pass
    r = sandbox.execute("shell", command="ls ~/JARVIS-MKII/core")
    print(f"ls test: {'PASS' if r['ok'] else 'FAIL'} — {r.get('result','')[:80]}")

    # Should be denied — blocked path
    r = sandbox.execute("file_read", path="/etc/passwd")
    print(f"passwd test: {'BLOCKED' if not r['ok'] else 'FAIL — should be blocked'}")

    # Should be denied — blocked command
    r = sandbox.execute("shell", command="sudo rm -rf /")
    print(f"sudo test: {'BLOCKED' if not r['ok'] else 'FAIL — should be blocked'}")

    sandbox.status()
