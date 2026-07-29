"""
NetReaper - Target profile persistence
Author: 09azo14 | License: MIT
"""

import json
import datetime
from pathlib import Path

PROFILE_PATH = Path(__file__).parent.parent / "data" / "target_profile.json"


class TargetProfile:
    """Stores and updates target information across scans."""

    def __init__(self):
        self.data = {
            "targets": {}
        }
        self._load()

    def _load(self):
        if PROFILE_PATH.exists():
            try:
                with open(PROFILE_PATH, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"targets": {}}

    def _save(self):
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_PATH, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_target(self, target: str) -> dict:
        return self.data.get("targets", {}).get(target, {})

    def update_target(self, target: str, **kwargs):
        if "targets" not in self.data:
            self.data["targets"] = {}
        if target not in self.data["targets"]:
            self.data["targets"][target] = {
                "ip": target,
                "first_seen": datetime.datetime.now().isoformat(),
                "ports": [],
                "os": "",
                "services": [],
                "notes": "",
            }
        profile = self.data["targets"][target]
        for k, v in kwargs.items():
            if k == "ports" and isinstance(v, list):
                existing = set(profile.get("ports", []))
                existing.update(v)
                profile["ports"] = sorted(existing, key=lambda x: int(str(x).rsplit("/", 1)[-1]))
            elif k == "services" and isinstance(v, list):
                existing = profile.get("services", [])
                profile["services"] = existing + [s for s in v if s not in existing]
            elif v is not None:
                profile[k] = v
        profile["last_seen"] = datetime.datetime.now().isoformat()
        self._save()

    def add_ports(self, target: str, ports: list):
        self.update_target(target, ports=ports)

    def set_os(self, target: str, os: str):
        self.update_target(target, os=os)

    def add_services(self, target: str, services: list):
        self.update_target(target, services=services)

    def add_note(self, target: str, note: str):
        profile = self.get_target(target)
        current = profile.get("notes", "")
        self.update_target(target, notes=f"{current}\n- {note}" if current else note)

    def list_targets(self) -> list:
        return list(self.data.get("targets", {}).keys())

    def show(self, target: str) -> dict:
        return self.get_target(target)
