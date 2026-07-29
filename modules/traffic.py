"""
NetReaper - Traffic analysis module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from core.utils import run_command, select_interface, sanitize_for_shell
from core.platform import get_os, OS_WINDOWS, ensure_temp_dir

console = Console()


def run(action: str, logger) -> None:
    """Execute traffic analysis command."""
    os_type = get_os()
    if action == "interfaces":
        cmd = "ip link show" if os_type != OS_WINDOWS else "netsh interface show interface"
        output = run_command(cmd, logger=logger, module="traffic", target="local")
        logger.save_report("traffic_interfaces", output)
        return

    iface = select_interface()
    if not iface:
        return

    safe_iface = sanitize_for_shell(iface)
    temp_dir = ensure_temp_dir()
    out_file = temp_dir / f"traffic_{action}_{iface.replace(' ', '_')}"
    out_file_str = str(out_file).replace("'", "''") + ".pcap"

    if os_type == OS_WINDOWS:
        out_file_quoted = f'"{out_file_str}"'
        traffic_map = {
            "capture_all": f"tshark -i {safe_iface} -w {out_file_quoted}",
            "http": f"tshark -i {safe_iface} -Y http -T fields -e http.request.uri",
            "dns": f"tshark -i {safe_iface} -Y dns -T fields -e dns.qry.name",
            "creds": f"tshark -i {safe_iface} -Y 'http.authbasic or ftp.password or pop.password'",
            "arp": "arp -a",
            "live": "arp -a",
        }
    else:
        out_file_quoted = f"'{out_file_str}'"
        traffic_map = {
            "capture_all": f"tshark -i {safe_iface} -w {out_file_quoted}",
            "http": f"tshark -i {safe_iface} -Y 'http' -T fields -e http.request.uri",
            "dns": f"tshark -i {safe_iface} -Y 'dns' -T fields -e dns.qry.name",
            "creds": f"tshark -i {safe_iface} -Y 'http.authbasic or ftp.password or pop.password'",
            "arp": f"tcpdump -i {safe_iface} arp",
            "live": f"tcpdump -i {safe_iface} -n 'arp or icmp'",
        }

    if action not in traffic_map:
        console.print(f"[red] Unknown action: {action}[/]")
        return

    cmd = traffic_map[action]
    console.print(f"\n[bold cyan]-> Traffic: {action} on interface {iface}[/]")
    output = run_command(cmd, logger=logger, module="traffic", target=iface, timeout=60)
    logger.save_report(f"traffic_{action}_{iface}", output)
