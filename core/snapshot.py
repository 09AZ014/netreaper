"""
NetReaper - Structured scan snapshots
Author: 09azo14 | License: MIT

Converts raw scan output into a normalized, JSON-serializable structure so
that two scans can be compared semantically (hosts, ports, services, OS)
instead of as raw text.
"""

import json
import re
from pathlib import Path


def _empty_host() -> dict:
    return {"ports": {}, "services": {}, "os": "", "mac": ""}


def parse_nmap(output: str) -> dict:
    """Parse nmap -oN style output into {host: {...}}."""
    hosts: dict = {}
    current = None
    for line in output.splitlines():
        report = re.match(r"Nmap scan report for (.+)", line)
        if report:
            name = report.group(1).strip()
            ip_match = re.search(r"\(([^)]+)\)", name)
            current = ip_match.group(1).strip() if ip_match else name
            hosts.setdefault(current, _empty_host())
            continue

        if current is None:
            continue

        port = re.match(r"(\d+)/(\w+)\s+open\s*(\S*)\s*(.*)", line)
        if port:
            key = f"{port.group(1)}/{port.group(2)}"
            service = (port.group(3) or "").strip()
            version = (port.group(4) or "").strip()
            hosts[current]["ports"][key] = "open"
            hosts[current]["services"][key] = f"{service} {version}".strip()
            continue

        mac = re.match(r"MAC Address:\s+(\S+)", line, re.IGNORECASE)
        if mac:
            hosts[current]["mac"] = mac.group(1).lower()
            continue

        if "OS details:" in line:
            hosts[current]["os"] = line.split("OS details:", 1)[-1].strip()
        elif "Running:" in line:
            hosts[current]["os"] = line.split("Running:", 1)[-1].strip()

    return hosts


def parse_arp_scan(output: str) -> dict:
    """Parse arp-scan --localnet output into {host: {...}}."""
    hosts: dict = {}
    for line in output.splitlines():
        match = re.match(
            r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F:]{17})\s*(.*)", line
        )
        if match:
            host = match.group(1)
            hosts.setdefault(host, _empty_host())
            hosts[host]["mac"] = match.group(2).lower()
    return hosts


def parse_masscan(output: str) -> dict:
    """Parse masscan output into {host: {...}}."""
    hosts: dict = {}
    for line in output.splitlines():
        match = re.search(r"Discovered open port (\d+)/(\w+) on (\S+)", line)
        if match:
            host = match.group(3)
            key = f"{match.group(1)}/{match.group(2)}"
            hosts.setdefault(host, _empty_host())
            hosts[host]["ports"][key] = "open"
    return hosts


_PARSERS = (parse_nmap, parse_arp_scan, parse_masscan)


def build_snapshot(text: str) -> dict:
    """Build a structured snapshot from raw scan output of any supported tool."""
    hosts: dict = {}
    for parser in _PARSERS:
        for host, data in parser(text or "").items():
            merged = hosts.setdefault(host, _empty_host())
            merged["ports"].update(data.get("ports", {}))
            merged["services"].update(data.get("services", {}))
            if data.get("os"):
                merged["os"] = data["os"]
            if data.get("mac"):
                merged["mac"] = data["mac"]
    return {"hosts": hosts}


def has_hosts(snapshot: dict) -> bool:
    """Return True when the snapshot contains at least one parsed host."""
    return bool(snapshot.get("hosts"))


def to_json(snapshot: dict) -> str:
    """Serialize a snapshot to a JSON string."""
    return json.dumps(snapshot, indent=4, sort_keys=True)


def save_snapshot(snapshot: dict, path) -> Path:
    """Write a snapshot to disk as JSON and return the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(snapshot), encoding="utf-8")
    return path


def load_snapshot(path) -> dict:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
