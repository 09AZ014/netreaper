"""
NetReaper - Reconnaissance module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, sanitize_for_shell
from core.parser import extract_ports, extract_services, extract_os

console = Console()

SCAN_OPTIONS = {
    "ping_sweep":    "nmap -sn {target}/24",
    "arp_scan":      "arp-scan --localnet",
    "netdiscover":   "netdiscover -r {target}/24 -P",
    "masscan":       "masscan {target}/24 -p1-65535 --rate=1000",
    "fast_ports":    "nmap -F -T4 --open {target}",
    "full_ports":    "nmap -sS -p- -T3 --open {target}",
    "os_detect":     "nmap -A -T4 -sV --osscan-guess {target}",
    "stealth":       "nmap -sS -T2 -f --data-length 200 -D RND:5 {target}",
    "scripts":       "nmap -sC -sV {target}",
    "udp":           "nmap -sU --top-ports 200 -T3 {target}",
    "custom":        None,
}


def run(scan_type: str, target: str, logger, profile=None) -> None:
    """Execute recon command."""
    if scan_type not in SCAN_OPTIONS:
        console.print(f"[red] Unknown recon type: {scan_type}[/]")
        return

    safe_target = sanitize_for_shell(target)
    if scan_type == "custom":
        template = Prompt.ask("[cyan]Custom nmap command[/]", default="nmap -sV {target}")
        cmd = template.format(target=safe_target)
    elif scan_type in ("arp_scan",):
        cmd = SCAN_OPTIONS[scan_type]
    else:
        cmd = SCAN_OPTIONS[scan_type].format(target=safe_target)

    console.print(f"\n[bold cyan]-> Recon: {scan_type}[/]")
    output = run_command(cmd, logger=logger, module="recon", target=safe_target)
    logger.save_report(f"recon_{scan_type}_{target.replace('/', '_')}", output)

    if profile and output and scan_type != "arp_scan":
        current_os = profile.get_target(target).get("os", "")
        profile.update_target(
            target,
            ports=extract_ports(output),
            services=extract_services(output),
            os=extract_os(output) or current_os
        )
