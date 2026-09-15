"""
NetReaper - User configuration
Author: 09azo14 | License: MIT

Persistent preferences for NetReaper. Values are loaded from
data/config.json and can be overridden per-process with environment
variables. Missing keys always fall back to the defaults defined here.
"""

import copy
import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"

DEFAULTS: dict = {
    "target": "",
    "interface": "",
    "wordlist": "",
    "wordlist_dir": "",
    "timeouts": {
        "command": 300,
        "scan": 900,
        "install": 420,
    },
    "nvd_api_key": "",
    "learning_mode": False,
    "watch_interval": 300,
    "watch_webhook": "",
}

# Environment variable overrides, applied on top of the file values.
ENV_MAP = {
    "target": "NETREAPER_TARGET",
    "interface": "NETREAPER_INTERFACE",
    "wordlist": "NETREAPER_WORDLIST",
    "wordlist_dir": "NETREAPER_WORDLIST_DIR",
    "nvd_api_key": "NETREAPER_NVD_API_KEY",
    "learning_mode": "NETREAPER_LEARNING_MODE",
    "watch_interval": "NETREAPER_WATCH_INTERVAL",
    "watch_webhook": "NETREAPER_WATCH_WEBHOOK",
}

_TRUTHY = {"1", "true", "yes", "on"}


class Config:
    """Load, inspect and persist NetReaper configuration."""

    def __init__(self, path=None):
        self.path = Path(path) if path else CONFIG_PATH
        self.data: dict = copy.deepcopy(DEFAULTS)
        self._load()
        self._apply_env()

    def _load(self):
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (OSError, ValueError):
            return
        if isinstance(loaded, dict):
            self._merge(loaded)

    def _merge(self, loaded):
        for key, value in loaded.items():
            if key == "timeouts" and isinstance(value, dict):
                self.data.setdefault("timeouts", {}).update(value)
            else:
                self.data[key] = value

    def _apply_env(self):
        for key, env_name in ENV_MAP.items():
            raw = os.environ.get(env_name)
            if raw is None or raw == "":
                continue
            if key == "learning_mode":
                self.data[key] = raw.strip().lower() in _TRUTHY
            else:
                self.data[key] = raw

    def get(self, key, default=None):
        """Return a configuration value, falling back to the built-in defaults."""
        if key in self.data:
            return self.data[key]
        if key in DEFAULTS:
            return DEFAULTS[key]
        return default

    def get_timeout(self, name: str = "command") -> int:
        """Return a named timeout in seconds, coerced to a positive integer."""
        timeouts = self.data.get("timeouts", {})
        raw = timeouts.get(name, DEFAULTS["timeouts"].get(name, 300))
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return DEFAULTS["timeouts"].get(name, 300)
        return value if value > 0 else DEFAULTS["timeouts"].get(name, 300)

    def set(self, key: str, value, save: bool = True):
        """Set a configuration value, optionally persisting it."""
        self.data[key] = value
        if save:
            self.save()
        return value

    def update(self, **kwargs):
        """Update several values at once and persist them."""
        for key, value in kwargs.items():
            if value is not None:
                self.data[key] = value
        self.save()
        return self.data

    def save(self) -> Path:
        """Write the current configuration to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=4, sort_keys=True)
        return self.path

    def all(self) -> dict:
        """Return a copy of the full configuration."""
        return copy.deepcopy(self.data)

    def as_text(self) -> str:
        """Return a human-readable summary, with the API key masked."""
        lines = [f"Config file: {self.path}"]
        for key in DEFAULTS:
            value = self.data.get(key)
            if key == "nvd_api_key" and value:
                value = "*** set ***"
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)


_CONFIG = None


def get_config() -> Config:
    """Return the process-wide configuration instance."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG


def load_config(path=None) -> Config:
    """Load a configuration from an explicit path."""
    return Config(path)


def reset_config() -> Config:
    """Discard the cached configuration and reload it from disk."""
    global _CONFIG
    _CONFIG = Config()
    return _CONFIG


def config_path() -> Path:
    """Return the default configuration file path."""
    return CONFIG_PATH
