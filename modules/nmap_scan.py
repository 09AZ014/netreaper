"""
NetReaper - Nmap scan module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, sanitize_for_shell
from core.platform import ensure_temp_dir
from core.parser import extract_ports, extract_services, extract_os

console = Console()

SCAN_PROFILES = {
    "ping_sweep":  ("Ping Sweep",           "nmap -sn {target}"),
    "fast_ports":  ("Fast Scan",            "nmap -F -T4 --open {target}"),
    "full_ports":  ("Full Scan",            "nmap -sS -p- -T3 --open {target}"),
    "os_detect":   ("OS/Version Detection", "nmap -A -T4 -sV --osscan-guess {target}"),
    "stealth":     ("Stealth Scan",         "nmap -sS -T2 -f --data-length 200 -D RND:5 {target}"),
    "scripts":     ("NSE Scripts",          "nmap -sC -sV {target}"),
    "udp":         ("UDP Scan",             "nmap -sU --top-ports 200 -T3 {target}"),
    "custom":      ("Custom",               None),
}


def run(scan_type: str, target: str, logger, profile=None) -> None:
    """Execute nmap scan based on type."""
    if scan_type not in SCAN_PROFILES:
        console.print(f"[red] Unknown scan type: {scan_type}[/]")
        return

    safe_target = sanitize_for_shell(target)
    name, cmd_template = SCAN_PROFILES[scan_type]
    console.print(f"\n[bold cyan]-> {name} on {target}[/]")

    if scan_type == "custom":
        flags = sanitize_for_shell(Prompt.ask("[cyan]Custom nmap flags[/]", default="-sV -T3"))
        cmd = f"nmap {flags} {safe_target}"
    else:
        cmd = cmd_template.format(target=safe_target)

    # Output file
    temp_dir = ensure_temp_dir()
    out_file = temp_dir / f"{scan_type}_{target.replace('/', '_')}.txt"
    out_file_quoted = sanitize_for_shell(str(out_file))
    cmd += f" -oN {out_file_quoted}"

    output = run_command(cmd, logger=logger, module="nmap_scan", target=safe_target)
    logger.save_report(f"nmap_{scan_type}_{target.replace('/', '_')}", output)

    # Update target profile if available
    if profile and output:
        current_os = profile.get_target(target).get("os", "")
        profile.update_target(
            target,
            ports=extract_ports(output),
            services=extract_services(output),
            os=extract_os(output) or current_os
        )
