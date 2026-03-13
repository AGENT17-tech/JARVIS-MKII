import subprocess
import os
import glob

# ── Tool definitions — sent to Ollama so it knows what's available ──
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application on the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {
                        "type": "string",
                        "description": "Application to open e.g. firefox, code, gnome-terminal, nautilus, spotify"
                    }
                },
                "required": ["app"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_control",
            "description": "Control system power state",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["shutdown", "reboot", "sleep", "lock"],
                        "description": "Power action to perform"
                    },
                    "delay": {
                        "type": "integer",
                        "description": "Delay in seconds before action (default 0)"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_operation",
            "description": "Perform file operations — search, read, or open files",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["search", "read", "open"],
                        "description": "Operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "File path or search pattern e.g. ~/Documents/*.pdf"
                    }
                },
                "required": ["operation", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_script",
            "description": "Run a shell script or terminal command",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    }
]

# ── Action executors ────────────────────────────────────────────────

def open_app(app: str) -> str:
    try:
        subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Launched {app} successfully, sir."
    except FileNotFoundError:
        try:
            subprocess.Popen(["xdg-open", app])
            return f"Opened {app}, sir."
        except Exception:
            return f"Unable to locate {app} on this system, sir."

def system_control(action: str, delay: int = 0) -> str:
    # Defensively cast delay — Ollama sometimes passes it as a string
    try:
        delay = int(delay)
    except (TypeError, ValueError):
        delay = 0

    delay_mins = delay // 60 if delay > 0 else 0

    commands = {
        "shutdown": f"shutdown -h +{delay_mins}" if delay_mins else "shutdown -h now",
        "reboot":   f"shutdown -r +{delay_mins}" if delay_mins else "shutdown -r now",
        "sleep":    "systemctl suspend",
        "lock":     "loginctl lock-session",
    }
    cmd = commands.get(action)
    if not cmd:
        return f"Unknown action: {action}, sir."
    if action in ["shutdown", "reboot"]:
        result = subprocess.run(["sudo", "-n"] + cmd.split(), capture_output=True)
        if result.returncode != 0:
            return f"Insufficient privileges for {action}, sir. Please configure sudo access."
    else:
        subprocess.Popen(cmd.split())
    return f"Executing {action}, sir."

def file_operation(operation: str, path: str) -> str:
    expanded = os.path.expanduser(path)
    if operation == "search":
        matches = glob.glob(expanded, recursive=True)
        if not matches:
            return f"No files found matching {path}, sir."
        return "Found: " + ", ".join(matches[:5])
    elif operation == "read":
        try:
            with open(expanded, 'r') as f:
                content = f.read(2000)
            return f"Contents of {path}:\n{content}"
        except Exception as e:
            return f"Unable to read {path}: {str(e)}"
    elif operation == "open":
        subprocess.Popen(["xdg-open", expanded])
        return f"Opening {path}, sir."
    return "Unknown file operation."

def run_script(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Command executed successfully, sir."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds, sir."
    except Exception as e:
        return f"Command failed: {str(e)}"

# ── Dispatcher ──────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> str:
    if name == "open_app":
        return open_app(**args)
    elif name == "system_control":
        return system_control(**args)
    elif name == "file_operation":
        return file_operation(**args)
    elif name == "run_script":
        return run_script(**args)
    return "Unknown tool, sir."
