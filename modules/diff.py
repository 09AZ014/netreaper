"""
NetReaper - Scan diff module
Author: 09azo14 | License: MIT

Compares two saved scan reports. When both reports contain recognizable
host data the comparison is semantic (hosts, ports, services, OS); otherwise
it falls back to a raw text diff.
"""

import difflib
from pathlib import Path
from rich.console import Console

from core.snapshot import build_snapshot, has_hosts

console = Console()
REPORTS_DIR = Path(__file__).parent.parent / "reports"

TEXT_EXTS = {".txt", ".log"}


def list_reports() -> list:
    """Return all saved text reports, newest session first."""
    reports = []
    if REPORTS_DIR.exists():
        for session_dir in sorted(REPORTS_DIR.iterdir(), reverse=True):
            if session_dir.is_dir():
                for f in session_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in TEXT_EXTS:
                        reports.append(str(f))
    return reports


def build_snapshot_from_report(path) -> dict:
    """Parse a saved report file into a structured snapshot."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        console.print(f"[red] Error reading {path}: {e}[/]")
        return {"hosts": {}}
    return build_snapshot(text)


def diff_snapshots(base: dict, new: dict) -> dict:
    """Compute the semantic differences between two snapshots."""
    result: dict = {"hosts_added": [], "hosts_removed": [], "hosts_changed": {}}

    base_hosts = base.get("hosts", {})
    new_hosts = new.get("hosts", {})

    result["hosts_added"] = sorted(set(new_hosts) - set(base_hosts))
    result["hosts_removed"] = sorted(set(base_hosts) - set(new_hosts))

    for host in sorted(set(base_hosts) & set(new_hosts)):
        before = base_hosts[host]
        after = new_hosts[host]
        changes: dict = {}

        ports_added = sorted(set(after.get("ports", {})) - set(before.get("ports", {})))
        ports_removed = sorted(set(before.get("ports", {})) - set(after.get("ports", {})))
        if ports_added:
            changes["ports_added"] = ports_added
        if ports_removed:
            changes["ports_removed"] = ports_removed

        services_changed = {}
        for key in sorted(set(before.get("services", {})) & set(after.get("services", {}))):
            old = before["services"][key]
            new_val = after["services"][key]
            if old != new_val:
                services_changed[key] = {"from": old, "to": new_val}
        if services_changed:
            changes["services_changed"] = services_changed

        if before.get("os") and after.get("os") and before["os"] != after["os"]:
            changes["os_changed"] = {"from": before["os"], "to": after["os"]}

        if changes:
            result["hosts_changed"][host] = changes

    return result


def is_empty_diff(result: dict) -> bool:
    """Return True when no semantic differences were detected."""
    return not (
        result.get("hosts_added")
        or result.get("hosts_removed")
        or result.get("hosts_changed")
    )


def format_semantic_diff(result: dict) -> str:
    """Render a semantic diff to a plain-text string."""
    lines = []

    if is_empty_diff(result):
        return "No changes detected between the two scans."

    for host in result.get("hosts_added", []):
        lines.append(f"[+] New host discovered: {host}")
    for host in result.get("hosts_removed", []):
        lines.append(f"[-] Host no longer responding: {host}")

    for host, changes in sorted(result.get("hosts_changed", {}).items()):
        lines.append(f"[*] Changes on {host}:")
        for port in changes.get("ports_added", []):
            lines.append(f"    [+] port opened: {port}")
        for port in changes.get("ports_removed", []):
            lines.append(f"    [-] port closed: {port}")
        for port, change in sorted(changes.get("services_changed", {}).items()):
            lines.append(f"    [~] service {port}: {change['from']} -> {change['to']}")
        if "os_changed" in changes:
            os_change = changes["os_changed"]
            lines.append(f"    [~] os: {os_change['from']} -> {os_change['to']}")

    return "\n".join(lines)


def _print_semantic(result: dict) -> None:
    if is_empty_diff(result):
        console.print("[green] No changes detected between the two scans.[/]")
        return

    for host in result.get("hosts_added", []):
        console.print(f"[green][+] New host discovered: {host}[/]")
    for host in result.get("hosts_removed", []):
        console.print(f"[red][-] Host no longer responding: {host}[/]")

    for host, changes in sorted(result.get("hosts_changed", {}).items()):
        console.print(f"[bold yellow][*] Changes on {host}:[/]")
        for port in changes.get("ports_added", []):
            console.print(f"    [green][+] port opened: {port}[/]")
        for port in changes.get("ports_removed", []):
            console.print(f"    [red][-] port closed: {port}[/]")
        for port, change in sorted(changes.get("services_changed", {}).items()):
            console.print(
                f"    [yellow][~] service {port}: "
                f"{change['from']} -> {change['to']}[/]"
            )
        if "os_changed" in changes:
            os_change = changes["os_changed"]
            console.print(
                f"    [yellow][~] os: {os_change['from']} -> {os_change['to']}[/]"
            )


def format_text_diff(lines_a: list, lines_b: list, file_a: str, file_b: str) -> str:
    """Render a raw unified text diff."""
    diff = difflib.unified_diff(
        lines_a, lines_b,
        fromfile=file_a,
        tofile=file_b,
        lineterm=""
    )
    return "\n".join(diff)


def _print_text_diff(diff_output: str) -> None:
    for line in diff_output.splitlines():
        if line.startswith("+"):
            console.print(f"[green]{line}[/]")
        elif line.startswith("-"):
            console.print(f"[red]{line}[/]")
        elif line.startswith("@@"):
            console.print(f"[yellow]{line}[/]")
        else:
            console.print(line)


def compare(file_a: str, file_b: str) -> str:
    """Compare two report files and return the rendered diff as text."""
    snapshot_a = build_snapshot_from_report(file_a)
    snapshot_b = build_snapshot_from_report(file_b)

    if has_hosts(snapshot_a) and has_hosts(snapshot_b):
        result = diff_snapshots(snapshot_a, snapshot_b)
        _print_semantic(result)
        return format_semantic_diff(result)

    try:
        with open(file_a, "r", encoding="utf-8", errors="replace") as fa, \
                open(file_b, "r", encoding="utf-8", errors="replace") as fb:
            lines_a = fa.readlines()
            lines_b = fb.readlines()
    except OSError as e:
        console.print(f"[red] Error reading files: {e}[/]")
        return ""

    diff_output = format_text_diff(lines_a, lines_b, file_a, file_b)
    _print_text_diff(diff_output)
    return diff_output


def run(logger=None) -> None:
    """Interactively compare two saved reports."""
    reports = list_reports()
    if len(reports) < 2:
        console.print("[yellow] At least two reports are needed to compare.[/]")
        return

    import questionary
    file_a = questionary.select("Base report:", choices=reports).ask()
    file_b = questionary.select("Report to compare:", choices=reports).ask()

    if not file_a or not file_b or file_a == file_b:
        console.print("[red] Select two different reports.[/]")
        return

    console.print("\n[bold cyan]== Scan Diff ==[/]")
    diff_output = compare(file_a, file_b)

    if logger:
        logger.save_report("scan_diff", diff_output)
