"""
NetReaper - Continuous scan watch mode
Author: 09azo14 | License: MIT

Re-runs a scan on a fixed interval and raises an alert when the result differs
from the previous run. Two comparison strategies are used:

* Semantic diff when the output is host/port oriented (recon, nmap, and the
  nmap-backed vulnerability scans). Reports new hosts, opened/closed ports,
  service version changes and OS changes.
* Findings diff otherwise (web scanners, sslscan, lynis, enum4linux). Reports
  individual result lines that appeared or disappeared, after filtering out
  progress noise and volatile values such as timestamps and HTTP Date headers.
"""

import datetime
import importlib
import json
import re
import time
import urllib.request

from rich.console import Console

from core.config import get_config
from core.snapshot import build_snapshot, has_hosts
from modules import diff

console = Console()

# Watchable commands mapped to (module name, action mapping, accepts_profile).
WATCH_MODULES = {
    "recon": ("modules.recon", "SCAN_OPTIONS", True),
    "nmap": ("modules.nmap_scan", "SCAN_PROFILES", True),
    "web": ("modules.web", "WEB_OPTIONS", False),
    "vuln": ("modules.vuln", "VULN_SCANS", False),
}

DEFAULT_INTERVAL = 300

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?")
_HTTP_DATE_RE = re.compile(r"\b[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} GMT\b")
_DURATION_RE = re.compile(r"\(\s*[\d.]+ ?(?:s|ms|sec|min)\s*\)", re.IGNORECASE)
_SEPARATOR_RE = re.compile(r"^[\s\-=*#_|+<>.]+$")
# Nikto ends with a request/error counter that changes on every run.
_COUNTER_RE = re.compile(r"^[+\-]?\s*\d+\s+requests?:\s+\d+\s+error", re.IGNORECASE)

# Response headers that change on every request and would cause false alerts.
VOLATILE_HEADER_PREFIXES = (
    "date:", "age:", "expires:", "etag:", "last-modified:", "set-cookie:",
    "x-request-id:", "x-amz-request-id:", "cf-ray:", "server-timing:",
    "x-cache:", "x-timer:", "x-transaction-id:",
)

# Lines that describe progress or tool banners rather than findings.
NOISE_SUBSTRINGS = (
    "scan initiated",
    "nmap done:",
    "starting nmap",
    "starting arp-scan",
    "packets received by filter",
    "starting gobuster",
    "progress:",
    "waiting for cache lock",
)


def available_actions(command: str) -> list:
    """Return the sorted action names that can be watched for a command."""
    module_name, mapping_name, _ = WATCH_MODULES[command]
    module = importlib.import_module(module_name)
    return sorted(getattr(module, mapping_name).keys())


def resolve_interval(value=None) -> int:
    """Return a positive watch interval in seconds."""
    if value is None:
        value = get_config().get("watch_interval", DEFAULT_INTERVAL)
    try:
        interval = int(value)
    except (TypeError, ValueError):
        return DEFAULT_INTERVAL
    return interval if interval > 0 else DEFAULT_INTERVAL


def normalise_line(raw: str) -> str:
    """Strip ANSI codes, timestamps and durations, then collapse whitespace."""
    line = _ANSI_RE.sub("", raw or "")
    line = _TIMESTAMP_RE.sub("", line)
    line = _HTTP_DATE_RE.sub("", line)
    line = _DURATION_RE.sub("", line)
    return re.sub(r"\s+", " ", line).strip()


def is_noise(line: str) -> bool:
    """Return True when a normalised line carries no finding information."""
    if not line or len(line) < 2:
        return True
    if _SEPARATOR_RE.match(line):
        return True
    if _COUNTER_RE.match(line):
        return True
    lowered = line.lower()
    if any(marker in lowered for marker in NOISE_SUBSTRINGS):
        return True
    return any(lowered.startswith(prefix) for prefix in VOLATILE_HEADER_PREFIXES)


def extract_findings(output: str) -> list:
    """Extract normalised, de-duplicated finding lines from tool output."""
    findings = set()
    for raw in (output or "").splitlines():
        line = normalise_line(raw)
        if is_noise(line):
            continue
        findings.add(line)
    return sorted(findings)


def _run_scan(command: str, action: str, target: str, logger, profile=None) -> None:
    """Run a single scan through the module that owns the action."""
    module_name, _, accepts_profile = WATCH_MODULES[command]
    module = importlib.import_module(module_name)
    if accepts_profile:
        module.run(action, target, logger, profile)
    else:
        module.run(action, target, logger)


def capture_state(command, action, target, logger, profile=None) -> dict:
    """
    Run one scan and capture both a host snapshot and a findings list.

    The output is read back from the logger's command history, so no module
    needs to change its return value to support watch mode.
    """
    commands = getattr(logger, "commands", None)
    before = len(commands) if commands is not None else 0
    _run_scan(command, action, target, logger, profile)
    entries = getattr(logger, "commands", [])[before:]
    output = "\n".join(entry.get("output", "") for entry in entries)

    state = build_snapshot(output)
    state["findings"] = extract_findings(output)
    return state


def has_state(state: dict) -> bool:
    """Return True when the state contains anything worth comparing."""
    return has_hosts(state) or bool(state.get("findings"))


def diff_findings(previous: list, current: list) -> dict:
    """Compare two findings lists and return what was added or removed."""
    prev = set(previous or [])
    cur = set(current or [])
    return {
        "findings_added": sorted(cur - prev),
        "findings_removed": sorted(prev - cur),
    }


def is_findings_diff(result: dict) -> bool:
    """Return True when a result came from the findings comparison."""
    return "findings_added" in result or "findings_removed" in result


def compare_states(previous: dict, current: dict) -> dict:
    """Compare two captured states using the most suitable strategy."""
    if has_hosts(previous) and has_hosts(current):
        return diff.diff_snapshots(previous, current)
    return diff_findings(previous.get("findings", []), current.get("findings", []))


def is_empty_change(result: dict) -> bool:
    """Return True when a comparison result contains no differences."""
    if is_findings_diff(result):
        return not result.get("findings_added") and not result.get("findings_removed")
    return diff.is_empty_diff(result)


def format_change(result: dict) -> str:
    """Render a comparison result as plain text."""
    if is_findings_diff(result):
        lines = [f"[+] {line}" for line in result.get("findings_added", [])]
        lines += [f"[-] {line}" for line in result.get("findings_removed", [])]
        return "\n".join(lines) if lines else "No changes detected."
    return diff.format_semantic_diff(result)


def send_webhook(url: str, payload: dict, timeout: int = 10) -> bool:
    """POST a JSON alert to a webhook URL. Returns True on a 2xx response."""
    if not url:
        return False
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "NetReaper/1.0.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= getattr(response, "status", 0) < 300
    except Exception as e:
        console.print(f"[yellow] Webhook delivery failed: {e}[/]")
        return False


def build_alert(result, target, iteration) -> dict:
    """Build the alert payload describing a detected change."""
    return {
        "source": "netreaper",
        "event": "scan_change",
        "kind": "findings" if is_findings_diff(result) else "semantic",
        "target": target,
        "iteration": iteration,
        "timestamp": datetime.datetime.now().isoformat(),
        "changes": format_change(result),
        "summary": result,
    }


def emit_alert(result, target, iteration, logger=None, webhook=None) -> dict:
    """Print an alert, save it to the session, and optionally POST it."""
    text = format_change(result)
    console.print(f"\n[bold red] Change detected on {target} (run #{iteration})[/]")
    for line in text.splitlines():
        console.print(f"  [yellow]{line}[/]")

    if logger is not None and hasattr(logger, "save_report"):
        logger.save_report(f"watch_change_run{iteration}", text)

    payload = build_alert(result, target, iteration)
    if webhook and send_webhook(webhook, payload):
        console.print("[green] Webhook alert delivered.[/]")
    return payload


def run(command, action, target, logger, interval=None, max_iterations=0,
        webhook=None, profile=None, sleep_fn=None) -> int:
    """
    Watch a scan: run it, compare against the previous run, and alert on
    changes. Repeats every `interval` seconds until interrupted or
    `max_iterations` runs have completed (0 means run forever).

    Returns the number of change events detected.
    """
    if command not in WATCH_MODULES:
        console.print(f"[red] Cannot watch unknown command: {command}[/]")
        return 0

    interval = resolve_interval(interval)
    if webhook is None:
        webhook = get_config().get("watch_webhook") or None
    sleep = sleep_fn or time.sleep

    console.print(
        f"[bold cyan] Watch mode started:[/] {command} {action} on {target}"
        f" every {interval}s"
    )
    if max_iterations:
        console.print(f"[dim] Limited to {max_iterations} run(s).[/]")

    iteration = 0
    previous = None
    changes = 0
    try:
        while True:
            iteration += 1
            stamp = datetime.datetime.now().isoformat()
            console.print(f"\n[bold]Watch run #{iteration}[/] - {stamp}")
            state = capture_state(command, action, target, logger, profile)

            if not has_state(state):
                console.print("[yellow] No comparable data in this run; skipping comparison.[/]")
            elif previous is None:
                console.print("[dim] Baseline captured. Watching for changes...[/]")
            else:
                result = compare_states(previous, state)
                if is_empty_change(result):
                    console.print("[green] No changes detected.[/]")
                else:
                    changes += 1
                    emit_alert(result, target, iteration, logger, webhook)

            if has_state(state):
                previous = state

            if max_iterations and iteration >= max_iterations:
                break

            console.print(f"[dim] Next run in {interval}s. Press Ctrl+C to stop.[/]")
            sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow] Watch mode stopped by user.[/]")

    console.print(
        f"[bold]Watch finished:[/] {iteration} run(s), {changes} change event(s)."
    )
    return changes
