"""
NetReaper - Cross-platform detection and command abstraction
Author: 09azo14 | License: MIT
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

# Known operating systems
OS_WINDOWS = "windows"
OS_LINUX = "linux"
OS_MACOS = "darwin"
OS_UNKNOWN = "unknown"


def get_os() -> str:
    """Detect the operating system where NetReaper is running."""
    system = platform.system().lower()
    if system == "windows":
        return OS_WINDOWS
    elif system == "linux":
        return OS_LINUX
    elif system == "darwin":
        return OS_MACOS
    return OS_UNKNOWN


def is_windows() -> bool:
    return get_os() == OS_WINDOWS


def is_linux() -> bool:
    return get_os() == OS_LINUX


def is_macos() -> bool:
    return get_os() == OS_MACOS


def os_label() -> str:
    """Return a friendly OS label for the UI."""
    return {
        OS_WINDOWS: "Windows",
        OS_LINUX: "Linux",
        OS_MACOS: "macOS",
    }.get(get_os(), "Unknown")


def get_temp_dir() -> Path:
    """Return a cross-platform temporary directory for NetReaper."""
    import tempfile
    return Path(tempfile.gettempdir()) / "netreaper"


def ensure_temp_dir() -> Path:
    """Ensure NetReaper temp directory exists."""
    temp = get_temp_dir()
    temp.mkdir(parents=True, exist_ok=True)
    return temp


def _get_interfaces_psutil() -> list:
    """Return interface names using psutil, if available."""
    try:
        import psutil
        return list(psutil.net_if_addrs().keys())
    except ImportError:
        return []


def get_local_interfaces() -> list:
    """Get list of network interfaces in a cross-platform way."""
    os_type = get_os()
    interfaces = []

    # Prefer psutil on Windows and macOS; fallback to CLI on Linux if not installed.
    if os_type in (OS_WINDOWS, OS_MACOS):
        psutil_ifaces = _get_interfaces_psutil()
        if psutil_ifaces:
            return psutil_ifaces

    if os_type == OS_WINDOWS:
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=30
            )
            lines = result.stdout.splitlines()
            # Skip header lines and the dashed separator
            data_started = False
            for line in lines:
                if not data_started:
                    if line.startswith("---"):
                        data_started = True
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    # Last column is the interface name
                    name = " ".join(parts[3:]).strip()
                    if name:
                        interfaces.append(name)
        except Exception:
            pass
    elif os_type in (OS_LINUX, OS_MACOS):
        try:
            result = subprocess.run(
                ["ip", "-o", "link", "show"], capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines():
                parts = line.split(":")
                if len(parts) >= 2:
                    name = parts[1].strip().split("@")[0]
                    if name != "lo":
                        interfaces.append(name)
        except Exception:
            pass

    # Fallback to psutil if no interfaces found
    if not interfaces:
        interfaces = _get_interfaces_psutil()

    return interfaces


def get_default_gateway() -> str:
    """Return default gateway, if detectable."""
    os_type = get_os()
    try:
        if os_type == OS_WINDOWS:
            result = subprocess.run(
                ["netsh", "interface", "ip", "show", "route"],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                # Look for a 0.0.0.0/0 route, gateway is usually the third column
                # parts[0] is the destination network printed by netsh, not a bind address.
                if len(parts) >= 3 and parts[0] == "0.0.0.0":  # nosec B104
                    return parts[2].strip()
        else:
            result = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines():
                if "default" in line:
                    parts = line.split()
                    if "via" in parts:
                        return parts[parts.index("via") + 1]
    except Exception:
        pass
    return ""


def get_local_ip() -> str:
    """Return a best-effort local IP address."""
    os_type = get_os()
    try:
        if os_type == OS_WINDOWS:
            # Try psutil first for a reliable address
            try:
                import psutil
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family.name == "AF_INET":
                            return addr.address
            except ImportError:
                pass
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines():
                if "IPv4" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        return parts[-1].strip()
        else:
            result = subprocess.run(
                ["hostname", "-I"], capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                return result.stdout.strip().split()[0]
    except Exception:
        pass
    return ""


def get_package_managers() -> list:
    """Return available package managers for the current OS."""
    os_type = get_os()
    candidates = []
    if os_type == OS_WINDOWS:
        candidates = ["winget", "choco"]
    elif os_type == OS_MACOS:
        candidates = ["brew"]
    elif os_type == OS_LINUX:
        candidates = ["apt", "apt-get", "yum", "dnf", "pacman", "zypper"]
    return [pm for pm in candidates if shutil.which(pm)]


def get_firewall_status_cmd() -> str:
    """Return the appropriate firewall status command for the OS."""
    os_type = get_os()
    if os_type == OS_WINDOWS:
        return "netsh advfirewall show currentprofile"
    elif os_type == OS_MACOS:
        return "sudo pfctl -sr"
    return "iptables -L -n -v"


def get_connections_cmd() -> str:
    """Return command to list active connections."""
    os_type = get_os()
    if os_type == OS_WINDOWS:
        return "netstat -an"
    return "ss -tulnp"


def get_listening_cmd() -> str:
    """Return command to list listening ports."""
    os_type = get_os()
    if os_type == OS_WINDOWS:
        return "netstat -ano | findstr LISTENING"
    return "lsof -nP -iTCP -sTCP:LISTEN"


def get_arp_table_cmd() -> str:
    """Return command to show ARP table."""
    os_type = get_os()
    if os_type == OS_WINDOWS:
        return "arp -a"
    return "arp -a"


def supported_modules() -> dict:
    """Return a map of module -> whether it is supported on the current OS."""
    os_type = get_os()
    # Windows does not have iptables, aircrack-ng out of the box, etc.
    common = {
        "recon": True,
        "nmap_scan": True,
        "vuln": True,
        "exploit": True,
        "crack": True,
        "web": True,
        "traffic": True,
        "diff": True,
        "profile": True,
        "cve": True,
        "reports": True,
        "tools": True,
        "learn": True,
    }
    if os_type == OS_WINDOWS:
        common.update({
            "wireless": False,
            "defense": False,
        })
    else:
        common.update({
            "wireless": True,
            "defense": True,
        })
    return common


def command_for(command_key: str) -> str:
    """Return a platform-aware command string for common operations."""
    os_type = get_os()
    commands = {
        "ping": "ping" if os_type == OS_WINDOWS else "ping -c 4",
        "interfaces": (
            "ip link show" if os_type in (OS_LINUX, OS_MACOS)
            else "netsh interface show interface"
        ),
    }
    return commands.get(command_key, "")


def is_admin() -> bool:
    """Check if the current process has administrative/root privileges."""
    try:
        if is_windows():
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        return os.geteuid() == 0
    except Exception:
        return False
