"""
NetReaper - Defense and monitoring module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, confirm_action, sanitize_for_shell
from core.platform import get_os, OS_WINDOWS

console = Console()


def run(action: str, logger) -> None:
    """Execute defense/monitoring command."""
    os_type = get_os()
    if os_type == OS_WINDOWS:
        if action == "fw_status":
            cmd = "netsh advfirewall show currentprofile"
        elif action == "block_ip":
            # Placeholder shown to the operator, not a bind address.
            default_ip = "0.0.0.0"  # nosec B104
            ip = sanitize_for_shell(Prompt.ask("[cyan]IP to block[/]", default=default_ip))
            if not confirm_action(f"block IP {ip}"):
                return
            safe_ip = ip.replace("'", "''")
            rule_name = f"NetReaper_Block_{safe_ip.replace('.', '_')}"
            cmd = (
                f"netsh advfirewall firewall add rule name={rule_name} "
                f"dir=in action=block remoteip='{safe_ip}'"
            )
        elif action == "connections":
            cmd = "netstat -an"
        elif action == "arp_table":
            cmd = "arp -a"
        elif action == "failed_login":
            cmd = "wevtutil qe Security /q:\"*[System[(EventID=4625)]]\" /f:text /c:20"
        elif action == "processes":
            cmd = "tasklist /fo table /fi \"status eq running\""
        elif action == "fail2ban":
            console.print("[yellow] fail2ban is not available on Windows.[/]")
            return
        elif action == "listening":
            cmd = "netstat -ano | findstr LISTENING"
        else:
            console.print(f"[red] Unknown action: {action}[/]")
            return
    else:
        if action == "fw_status":
            cmd = "iptables -L -n -v"
        elif action == "block_ip":
            # Placeholder shown to the operator, not a bind address.
            default_ip = "0.0.0.0"  # nosec B104
            ip = sanitize_for_shell(Prompt.ask("[cyan]IP to block[/]", default=default_ip))
            if not confirm_action(f"block IP {ip}"):
                return
            cmd = f"sudo iptables -A INPUT -s {ip} -j DROP"
        elif action == "connections":
            cmd = "ss -tulnp"
        elif action == "arp_table":
            cmd = "arp -a"
        elif action == "failed_login":
            cmd = "grep 'Failed password' /var/log/auth.log | tail -20"
        elif action == "processes":
            cmd = "ps aux --sort=-%cpu | head -20"
        elif action == "fail2ban":
            cmd = "fail2ban-client status"
        elif action == "listening":
            cmd = "lsof -nP -iTCP -sTCP:LISTEN"
        else:
            console.print(f"[red] Unknown action: {action}[/]")
            return

    console.print(f"\n[bold cyan]-> Defense: {action}[/]")
    output = run_command(cmd, logger=logger, module="defense", target="local")
    logger.save_report(f"defense_{action}", output)
