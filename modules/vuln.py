"""
NetReaper - Vulnerability scanning module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, sanitize_for_shell

console = Console()

VULN_SCANS = {
    "nmap_vuln":     "nmap --script vuln {target}",
    "nmap_exploit":  "nmap --script exploit {target}",
    "nmap_auth":     "nmap --script auth {target}",
    "nmap_brute":    "nmap --script brute {target}",
    "ssl_vuln":      "sslscan --show-certificate {target}",
    "smb_enum":      "enum4linux -a {target}",
    "lynis":         "lynis audit system --no-colors",
    "searchsploit":  None,
}


def run(scan_type: str, target: str, logger) -> None:
    """Execute vulnerability scan."""
    if scan_type not in VULN_SCANS:
        console.print(f"[red] Unknown scan type: {scan_type}[/]")
        return

    safe_target = sanitize_for_shell(target)
    if scan_type == "searchsploit":
        query = sanitize_for_shell(
            Prompt.ask("[cyan]Service/version to search[/]", default="apache 2.4")
        )
        cmd = f"searchsploit {query}"
    elif scan_type == "lynis":
        cmd = VULN_SCANS[scan_type]
    else:
        cmd = VULN_SCANS[scan_type].format(target=safe_target)

    console.print(f"\n[bold cyan]-> Vuln scan: {scan_type}[/]")
    output = run_command(cmd, logger=logger, module="vuln", target=target)
    logger.save_report(f"vuln_{scan_type}_{target.replace('/', '_')}", output)
