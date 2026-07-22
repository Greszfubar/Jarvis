"""Load settings.yaml and .env into a single flat config dict."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / "config" / ".env")

with open(_ROOT / "config" / "settings.yaml") as f:
    _raw = yaml.safe_load(f)

# Merge top-level jarvis keys + all other sections into one dict
cfg: dict = _raw.get("jarvis", {}) | {k: v for k, v in _raw.items() if k != "jarvis"}


def env(key: str, default: str = "") -> str:
    """Config lookup: environment (.env included) first, then the Keychain
    vault for secret-shaped keys, then the default."""
    val = os.getenv(key, "")
    if val:
        return val
    from core.vault import is_secret_key, vault_get
    if is_secret_key(key):
        vaulted = vault_get(key)
        if vaulted:
            return vaulted
    return default
