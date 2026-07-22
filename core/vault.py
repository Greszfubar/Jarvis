"""
The vault — credentials in the macOS Keychain, never in plaintext files.

Backed by `security` (the Keychain CLI): encrypted at rest, unlocked with the
user session, invisible to the repo. Every secret is a generic password under
service "jarvis".

Usage:
    from core.vault import vault_get, vault_set
    token = vault_get("TELEGRAM_BOT_TOKEN")

Migration (moves KEY/TOKEN/SECRET entries out of config/.env, blanks them there):
    .venv/bin/python -m core.vault migrate
"""
import logging
import re
import subprocess
from pathlib import Path

log = logging.getLogger("jarvis.vault")

_SERVICE = "jarvis"
_SECRET_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)


def vault_get(name: str) -> str:
    """Return the secret, or '' if absent."""
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-s", _SERVICE, "-a", name, "-w"],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception as e:
        log.warning(f"vault_get({name}) failed: {e}")
        return ""


def vault_set(name: str, value: str) -> bool:
    """Store/overwrite a secret."""
    try:
        r = subprocess.run(
            ["security", "add-generic-password", "-s", _SERVICE, "-a", name,
             "-w", value, "-U"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception as e:
        log.error(f"vault_set({name}) failed: {e}")
        return False


def vault_delete(name: str) -> bool:
    try:
        r = subprocess.run(
            ["security", "delete-generic-password", "-s", _SERVICE, "-a", name],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def is_secret_key(key: str) -> bool:
    return bool(_SECRET_RE.search(key))


def migrate_env(env_path: Path = Path("config/.env")) -> list:
    """
    Move every secret-looking entry from config/.env into the Keychain and
    blank it in the file (the key stays as documentation of what exists).
    Returns the list of migrated key names.
    """
    if not env_path.exists():
        return []
    migrated = []
    out_lines = []
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, val = stripped.partition("=")
            key, val = key.strip(), val.strip()
            if val and is_secret_key(key) and not val.startswith("your_"):
                if vault_set(key, val):
                    migrated.append(key)
                    out_lines.append(f"{key}=")   # blanked — value now in Keychain
                    continue
        out_lines.append(line)
    if migrated:
        env_path.write_text("\n".join(out_lines) + "\n")
    return migrated


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        moved = migrate_env()
        print(f"Migrated to Keychain: {', '.join(moved) if moved else 'nothing to migrate'}")
    else:
        print(__doc__)
