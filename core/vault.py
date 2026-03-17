"""
vault.py — JARVIS MKIII Encrypted Secrets Vault
AES-256 via Fernet (cryptography library)
Secrets never touch the LLM raw.

Usage:
    from vault import vault
    vault.store("GMAIL_TOKEN", "your-token")
    token = vault.get("GMAIL_TOKEN")
"""

import os
import json
from cryptography.fernet import Fernet

VAULT_DIR      = os.path.expanduser("~/.jarvis")
VAULT_KEY_PATH = os.path.join(VAULT_DIR, "vault.key")
VAULT_PATH     = os.path.join(VAULT_DIR, "vault.enc")


class Vault:
    def __init__(self):
        os.makedirs(VAULT_DIR, exist_ok=True)
        self.key    = self._load_or_create_key()
        self.cipher = Fernet(self.key)
        self.data   = self._load()
        print("[VAULT] Initialized — secrets encrypted at rest.")

    # ── Key management ────────────────────────────────────────────────
    def _load_or_create_key(self) -> bytes:
        if os.path.exists(VAULT_KEY_PATH):
            with open(VAULT_KEY_PATH, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(VAULT_KEY_PATH, "wb") as f:
            f.write(key)
        os.chmod(VAULT_KEY_PATH, 0o600)   # owner read/write only
        print("[VAULT] New encryption key generated.")
        return key

    # ── Persistence ───────────────────────────────────────────────────
    def _load(self) -> dict:
        if not os.path.exists(VAULT_PATH):
            return {}
        try:
            with open(VAULT_PATH, "rb") as f:
                raw = f.read()
            return json.loads(self.cipher.decrypt(raw).decode())
        except Exception as e:
            print(f"[VAULT] Failed to load vault: {e}")
            return {}

    def _save(self):
        encrypted = self.cipher.encrypt(json.dumps(self.data).encode())
        with open(VAULT_PATH, "wb") as f:
            f.write(encrypted)
        os.chmod(VAULT_PATH, 0o600)

    # ── Public API ────────────────────────────────────────────────────
    def store(self, key: str, value: str):
        """Store a secret. Immediately persists to disk."""
        self.data[key] = value
        self._save()
        print(f"[VAULT] Stored: {key}")

    def get(self, key: str, default: str = "") -> str:
        """Retrieve a secret. Returns default if not found."""
        return self.data.get(key, default)

    def delete(self, key: str):
        """Remove a secret from the vault."""
        if key in self.data:
            del self.data[key]
            self._save()
            print(f"[VAULT] Deleted: {key}")

    def list_keys(self) -> list:
        """Return all stored key names (never values)."""
        return list(self.data.keys())

    def exists(self, key: str) -> bool:
        return key in self.data

    def inject(self, template: str) -> str:
        """
        Replace {{KEY_NAME}} placeholders in a string with vault values.
        Safe to use in tool configs — secrets injected at boundary, not stored raw.

        Example:
            url = vault.inject("https://api.example.com?key={{GEMINI_API_KEY}}")
        """
        import re
        def replacer(match):
            k = match.group(1)
            v = self.data.get(k, "")
            if not v:
                print(f"[VAULT] WARNING: Key '{k}' not found in vault.")
            return v
        return re.sub(r"\{\{(\w+)\}\}", replacer, template)

    def status(self):
        """Print vault status — keys only, never values."""
        print(f"[VAULT] Status: {len(self.data)} secret(s) stored.")
        for k in self.data:
            print(f"  - {k}")


# ── Singleton ─────────────────────────────────────────────────────────
vault = Vault()


# ── CLI utility ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 vault.py store KEY VALUE")
        print("  python3 vault.py get KEY")
        print("  python3 vault.py delete KEY")
        print("  python3 vault.py list")
        print("  python3 vault.py status")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "store" and len(sys.argv) == 4:
        vault.store(sys.argv[2], sys.argv[3])
        print(f"Stored '{sys.argv[2]}' successfully.")

    elif cmd == "get" and len(sys.argv) == 3:
        val = vault.get(sys.argv[2])
        if val:
            print(f"{sys.argv[2]} = {val}")
        else:
            print(f"Key '{sys.argv[2]}' not found.")

    elif cmd == "delete" and len(sys.argv) == 3:
        vault.delete(sys.argv[2])

    elif cmd == "list":
        keys = vault.list_keys()
        if keys:
            for k in keys:
                print(f"  {k}")
        else:
            print("Vault is empty.")

    elif cmd == "status":
        vault.status()

    else:
        print("Unknown command.")
