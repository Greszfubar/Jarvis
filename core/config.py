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
    return os.getenv(key, default)
