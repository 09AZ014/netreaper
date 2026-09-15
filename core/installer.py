"""
NetReaper - Dependency installer
Author: 09azo14 | License: MIT
"""

import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)

from core.platform import (
    get_os, get_package_managers, OS_WINDOWS, OS_MACOS
)

console = Console()

INSTALL_LOG_DIR = Path(__file__).parent.parent / "logs"
INSTALL_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Timing controls for the Debian/Ubuntu package manager path.
APT_LOCK_WAIT = 300        # Max seconds to wait for a busy apt/dpkg before installing.
APT_LOCK_TIMEOUT = 120     # Seconds apt itself should wait for the dpkg lock.
APT_INSTALL_TIMEOUT = 420  # Max seconds for a single install command.
APT_RECOVER_TIMEOUT = 300  # Max seconds for dpkg --configure -a / apt -f install.

# Package names are resolved per package manager. The "apt" entry is the
# Debian/Ubuntu name and is also used as the fallback for managers without an
# explicit entry. A value of None means the tool is known to be unavailable in
# that distribution's repositories, so installation is skipped cleanly instead
# of failing with a confusing "unable to locate package" error.
TOOLS = {
    "nmap":            {"apt": "nmap",                 "desc": "Network scanner"},
    "john":            {"apt": "john", "brew": "john-jumbo",
                        "desc": "Password cracker"},
    "hashcat":         {"apt": "hashcat",              "desc": "GPU hash cracker"},
    "hydra":           {"apt": "hydra",                "desc": "Network brute forcer"},
    "tshark":          {"apt": "tshark",               "dnf": "wireshark-cli",
                        "pacman": "wireshark-cli",     "desc": "CLI Wireshark"},
    "tcpdump":         {"apt": "tcpdump",              "desc": "Packet analyzer"},
    "aircrack-ng":     {"apt": "aircrack-ng",          "desc": "WiFi cracker"},
    "wifite":          {"apt": "wifite",               "dnf": None, "zypper": None,
                        "desc": "Auto WiFi attacker"},
    "nikto":           {"apt": "nikto",                "desc": "Web scanner"},
    "gobuster":        {"apt": "gobuster",             "desc": "Directory bruter"},
    "sqlmap":          {"apt": "sqlmap",               "desc": "SQL injection"},
    "searchsploit":    {"apt": "exploitdb",            "desc": "Exploit database"},
    "masscan":         {"apt": "masscan",              "desc": "Fast port scanner"},
    "arp-scan":        {"apt": "arp-scan",             "desc": "ARP network scanner"},
    "netdiscover":     {"apt": "netdiscover",          "dnf": None, "brew": None,
                        "desc": "Network discovery"},
    "sslscan":         {"apt": "sslscan",              "desc": "SSL/TLS scanner"},
    "enum4linux":      {"apt": "enum4linux",           "dnf": None, "brew": None,
                        "desc": "SMB enumeration"},
    "hping3":          {"apt": "hping3",               "pacman": "hping", "brew": "hping",
                        "desc": "Packet crafting"},
    "netcat":          {"apt": "netcat-openbsd",       "dnf": "nmap-ncat",
                        "pacman": "openbsd-netcat",    "cmd": "nc",
                        "desc": "Network utility"},
    "ffuf":            {"apt": "ffuf",                 "desc": "Web fuzzer"},
    "wfuzz":           {"apt": "wfuzz",                "desc": "Web fuzzer"},
    "dirb":            {"apt": "dirb",                 "desc": "Web content scanner"},
    "lynis":           {"apt": "lynis",                "desc": "System auditor"},
    "fail2ban-client": {"apt": "fail2ban",             "desc": "Intrusion prevention"},
    "bettercap":       {"apt": "bettercap",            "dnf": None, "zypper": None,
                        "desc": "Network attacker"},
    "ettercap":        {"apt": "ettercap-common",      "pacman": "ettercap", "brew": "ettercap",
                        "desc": "MITM tool"},
    "hashid":          {"apt": "hashid",               "dnf": None, "desc": "Hash identifier"},
    "msfconsole":      {"apt": "metasploit-framework", "dnf": None, "zypper": None,
                        "brew": None, "pacman": "metasploit", "desc": "Exploit framework"},
    "wireshark":       {"apt": "wireshark",            "pacman": "wireshark-qt",
                        "desc": "GUI packet analyzer"},
    "theHarvester":    {"apt": "theharvester",         "desc": "OSINT collector"},
    "smbclient":       {"apt": "smbclient",            "dnf": "samba-client",
                        "zypper": "samba-client", "brew": "samba", "desc": "SMB client"},
    "responder":       {"apt": "responder",            "dnf": None, "zypper": None, "brew": None,
                        "desc": "LLMNR/NBT-NS poisoner"},
    "crackmapexec":    {"apt": "crackmapexec",         "dnf": None, "zypper": None, "brew": None,
                        "desc": "Active Directory/SMB tool"},
}

PYTHON_DEPS = [
    "rich", "questionary", "InquirerPy", "fpdf2", "colorama",
    "tabulate", "requests", "paramiko",
]

# Package-manager aliases normalize vendor variants onto a single key.
_PM_ALIASES = {"apt-get": "apt", "yum": "dnf"}

# apt/dpkg processes that can hold the package cache lock.
APT_PROCESS_NAMES = (
    "apt", "apt-get", "dpkg", "dpkg-deb", "unattended-upgr", "aptd", "packagekitd",
)

# Output markers indicating another process holds the package manager lock.
LOCK_ERROR_MARKERS = (
    "could not get lock",
    "waiting for cache lock",
    "unable to acquire the dpkg frontend lock",
    "is another process using it",
    "lock-frontend",
)

# Output markers indicating dpkg was left in an interrupted state.
DPKG_RECOVERY_MARKERS = (
    "dpkg was interrupted",
    "dpkg --configure -a",
    "unmet dependencies",
    "you might want to run",
)


def _normalize_pm(pm: str) -> str:
    """Map a package manager name onto its canonical key."""
    if not pm:
        return pm
    return _PM_ALIASES.get(pm, pm)


def get_project_python_executable() -> str:
    """Return the project virtualenv Python interpreter when available."""
    project_root = Path(__file__).resolve().parents[1]
    candidates = (
        project_root / ".venv" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / ".venv" / "Scripts" / "python",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def get_package_manager() -> str:
    """Detect the system's package manager for the current OS."""
    pms = get_package_managers()
    return pms[0] if pms else None


def get_install_log_path() -> Path:
    """Return the path for the current install log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return INSTALL_LOG_DIR / f"install_{timestamp}.log"


def _log_install_event(log_path: Path, event: str, details: str = "") -> None:
    """Append an install event to the install log."""
    if not log_path:
        return
    timestamp = datetime.now().isoformat()
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {event}\n")
            if details:
                for line in details.splitlines():
                    f.write(f"    {line}\n")
    except OSError:
        pass


def _truncate_output(stdout: str, stderr: str = "", limit: int = 2000) -> str:
    """Return a truncated command output string."""
    return ((stdout or "") + (stderr or ""))[:limit]


def install_windows_tool(tool_name: str) -> tuple:
    """Try to install a tool on Windows using winget or chocolatey."""
    if shutil.which("winget"):
        try:
            result = subprocess.run(
                ["winget", "install", "--silent", "--id", tool_name],
                capture_output=True, text=True, timeout=300
            )
            return result.returncode == 0, _truncate_output(result.stdout, result.stderr)
        except Exception as exc:
            return False, str(exc)
    if shutil.which("choco"):
        try:
            result = subprocess.run(
                ["choco", "install", tool_name, "-y"],
                capture_output=True, text=True, timeout=300
            )
            return result.returncode == 0, _truncate_output(result.stdout, result.stderr)
        except Exception as exc:
            return False, str(exc)
    return False, "No supported Windows package manager found (winget/choco)"


def install_macos_tool(tool_name: str, pkg_name: str) -> tuple:
    """Install a tool on macOS using Homebrew."""
    if not shutil.which("brew"):
        return False, "Homebrew not found"
    try:
        result = subprocess.run(
            ["brew", "install", pkg_name],
            capture_output=True, text=True, timeout=300
        )
        return result.returncode == 0, _truncate_output(result.stdout, result.stderr)
    except Exception as exc:
        return False, str(exc)


def get_os_specific_pkg_name(tool_name: str, pm: str = None) -> str:
    """
    Return the distro-specific package name for a tool.

    Resolution order: an explicit entry for the detected package manager, then
    the Debian/Ubuntu name, then the tool name itself. Returns None when the
    tool is known to be unavailable for the given manager.
    """
    info = TOOLS.get(tool_name, {})
    os_type = get_os()

    if os_type == OS_MACOS:
        manager = "brew"
    elif pm:
        manager = _normalize_pm(pm)
    else:
        manager = None

    if manager and manager in info:
        return info[manager]

    return info.get("apt", tool_name)


def is_tool_installed(tool: str) -> bool:
    """Check if a CLI tool is installed using its executable name."""
    info = TOOLS.get(tool, {})
    executable = info.get("cmd", tool)
    return shutil.which(executable) is not None


def _is_root() -> bool:
    """Return True if the current process has root privileges."""
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _apt_env_prefix() -> list:
    """
    Build the privilege and environment prefix for apt/dpkg commands.

    Using `env VAR=value` instead of `sudo -E` avoids the
    "preserving the entire environment is not supported" warning and reliably
    applies the non-interactive settings that otherwise cause apt to block.
    """
    prefix = [] if _is_root() else ["sudo"]
    return prefix + [
        "env",
        "DEBIAN_FRONTEND=noninteractive",
        "APT_LISTCHANGES_FRONTEND=none",
        "NEEDRESTART_MODE=a",
    ]


def _apt_lock_holders() -> list:
    """Return the names of apt/dpkg processes currently holding the lock."""
    holders = []
    for name in APT_PROCESS_NAMES:
        try:
            result = subprocess.run(
                ["pgrep", "-x", name], capture_output=True, text=True, timeout=5
            )
        except Exception:
            continue
        if result.returncode == 0 and result.stdout.strip():
            holders.append(name)
    return holders


def wait_for_apt_lock(log_path: Path = None, timeout: int = APT_LOCK_WAIT,
                      poll_interval: int = 3) -> bool:
    """
    Wait until no other apt/dpkg process holds the package cache lock.

    Returns True when the lock is free, False if it is still held after the
    timeout. This prevents the installer from stalling indefinitely on the
    "Waiting for cache lock" state seen when another apt run is in progress.
    """
    deadline = time.monotonic() + timeout
    while True:
        holders = _apt_lock_holders()
        if not holders:
            return True
        if time.monotonic() >= deadline:
            _log_install_event(
                log_path, "APT LOCK TIMEOUT", f"still held by: {', '.join(holders)}"
            )
            console.print(
                f"[yellow] Package manager lock still held by: {', '.join(holders)}[/]"
            )
            return False
        time.sleep(poll_interval)


def _is_lock_error(output: str) -> bool:
    """Return True when apt output indicates a lock conflict."""
    text = (output or "").lower()
    return any(marker in text for marker in LOCK_ERROR_MARKERS)


def _needs_dpkg_recovery(output: str) -> bool:
    """Return True when apt output indicates an interrupted dpkg state."""
    text = (output or "").lower()
    return any(marker in text for marker in DPKG_RECOVERY_MARKERS)


def apt_recover(log_path: Path = None, pm: str = "apt-get") -> bool:
    """Repair an interrupted dpkg state and broken dependencies."""
    _log_install_event(log_path, "DPKG RECOVER START", "dpkg --configure -a")
    steps = (
        ["dpkg", "--configure", "-a"],
        [pm, "-f", "install", "-y"],
    )
    returncode = -1
    for step in steps:
        cmd = _apt_env_prefix() + step
        returncode, output = _run_install_command(cmd, timeout=APT_RECOVER_TIMEOUT)
        _log_install_event(
            log_path, "DPKG RECOVER STEP", f"{' '.join(step)} rc={returncode}\n{output[-1200:]}"
        )
    return returncode == 0


def _run_install_command(cmd: list, env: dict = None, timeout: int = 300) -> tuple:
    """
    Run an install command, stream output to the install log, and capture it.
    Returns (returncode, output).
    """
    output_lines = []
    proc = None
    timer = None

    def _kill_process():
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        timer = threading.Timer(timeout, _kill_process)
        timer.start()

        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if not line:
                    continue
                output_lines.append(line)
            returncode = proc.wait(timeout=5)
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            raise
        finally:
            if timer is not None:
                timer.cancel()
        return returncode, "\n".join(output_lines)
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return -1, str(exc)


def install_system_tool(tool_name: str, pkg_name: str, pm: str,
                        log_path: Path = None) -> tuple:
    """
    Install a system tool using the platform-specific package manager.

    On Debian/Ubuntu this waits for a free package lock, retries once after an
    interrupted dpkg state, and retries once after a lock conflict.
    """
    os_type = get_os()
    try:
        if os_type == OS_WINDOWS:
            return install_windows_tool(tool_name)
        if os_type == OS_MACOS:
            return install_macos_tool(tool_name, pkg_name or tool_name)

        manager = _normalize_pm(pm)

        if not pkg_name:
            return False, f"No {pm} package available for {tool_name}"

        if manager == "apt":
            base = _apt_env_prefix()
            cmd = base + [
                pm, "install", "-y",
                "-o", f"DPkg::Lock::Timeout={APT_LOCK_TIMEOUT}",
                "-o", "Dpkg::Options::=--force-confdef",
                "-o", "Dpkg::Options::=--force-confold",
                "--no-install-recommends",
                pkg_name,
            ]
        elif manager == "dnf":
            base = [] if _is_root() else ["sudo"]
            cmd = base + [pm, "install", "-y", pkg_name]
        elif manager == "pacman":
            base = [] if _is_root() else ["sudo"]
            cmd = base + ["pacman", "-S", "--noconfirm", pkg_name]
        elif manager == "zypper":
            base = [] if _is_root() else ["sudo"]
            cmd = base + ["zypper", "--non-interactive", "install", pkg_name]
        elif manager == "brew":
            cmd = ["brew", "install", pkg_name]
        else:
            return False, f"Unsupported package manager: {pm}"

        if manager == "apt":
            wait_for_apt_lock(log_path)

        returncode, output = _run_install_command(cmd, timeout=APT_INSTALL_TIMEOUT)

        if returncode != 0 and manager == "apt":
            if _needs_dpkg_recovery(output):
                _log_install_event(
                    log_path, f"DPKG RECOVERY TRIGGERED: {tool_name}", output[-1500:]
                )
                apt_recover(log_path, pm=pm)
                returncode, output = _run_install_command(cmd, timeout=APT_INSTALL_TIMEOUT)
            elif _is_lock_error(output):
                _log_install_event(
                    log_path, f"APT LOCK RETRY: {tool_name}", output[-1500:]
                )
                if wait_for_apt_lock(log_path):
                    returncode, output = _run_install_command(cmd, timeout=APT_INSTALL_TIMEOUT)

        return returncode == 0, _truncate_output(output)
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return False, str(exc)


def install_python_deps(log_path: Path = None) -> None:
    """Install Python package dependencies into the project interpreter."""
    python_executable = get_project_python_executable()
    total_deps = len(PYTHON_DEPS)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("Installing Python dependencies", total=total_deps)
        for dep in PYTHON_DEPS:
            progress.update(task, description=f"Installing Python dep: {dep}")
            try:
                result = subprocess.run(
                    [python_executable, "-m", "pip", "install", dep, "-q"],
                    capture_output=True, text=True, check=True, timeout=120
                )
                _log_install_event(
                    log_path,
                    f"PYTHON DEP INSTALLED: {dep}",
                    result.stdout[-1500:] if result.stdout else "",
                )
            except subprocess.CalledProcessError as exc:
                _log_install_event(
                    log_path,
                    f"PYTHON DEP FAILED: {dep}",
                    (exc.stdout or "")[-1500:] if exc.stdout else str(exc),
                )
            progress.advance(task)


def _update_package_lists(pm: str, install_log: Path) -> None:
    """Refresh the package lists for the detected manager, waiting for locks."""
    manager = _normalize_pm(pm)
    if manager == "apt":
        wait_for_apt_lock(install_log)
        cmd = _apt_env_prefix() + [
            pm, "update", "-qq",
            "-o", f"DPkg::Lock::Timeout={APT_LOCK_TIMEOUT}",
        ]
    elif manager == "dnf":
        prefix = [] if _is_root() else ["sudo"]
        cmd = prefix + [pm, "makecache", "-q"]
    elif manager == "pacman":
        prefix = [] if _is_root() else ["sudo"]
        cmd = prefix + ["pacman", "-Sy", "--noconfirm"]
    elif manager == "zypper":
        prefix = [] if _is_root() else ["sudo"]
        cmd = prefix + ["zypper", "--non-interactive", "refresh"]
    elif manager == "brew":
        cmd = ["brew", "update"]
    else:
        return

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        _log_install_event(
            install_log,
            "PACKAGE LIST UPDATE",
            f"returncode={result.returncode}\n{(result.stdout + result.stderr)[:1500]}",
        )
    except Exception as exc:
        _log_install_event(install_log, "PACKAGE LIST UPDATE FAILED", str(exc))


def check_and_install_deps(silent: bool = False, install_python: bool = True) -> dict:
    """
    Check all tools and install missing ones across supported OSes.
    Returns dict of {tool: installed_bool}
    """
    status = {}
    missing = []
    os_type = get_os()
    install_log = get_install_log_path()
    _log_install_event(install_log, "INSTALL START", f"OS: {os_type}")

    for tool, info in TOOLS.items():
        installed = is_tool_installed(tool)
        status[tool] = installed
        if not installed:
            missing.append((tool, info))

    if not silent:
        console.print(f"\n[bold cyan]Detected OS:[/] {os_type}")
        if missing:
            console.print(f"[yellow] {len(missing)} tools not found.[/]")

    if missing:
        pm = get_package_manager()
        if pm:
            if not silent:
                console.print(f"[cyan]Installing missing tools via {pm}...[/]\n")
                console.print(f"[dim]Install log: {install_log}[/]\n")

            unavailable = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                t = progress.add_task("Updating package lists", total=1)
                _update_package_lists(pm, install_log)
                progress.advance(t)

                task = progress.add_task("Installing system tools", total=len(missing))
                for tool, info in missing:
                    pkg_name = get_os_specific_pkg_name(tool, pm)
                    if not pkg_name:
                        unavailable.append(tool)
                        status[tool] = False
                        _log_install_event(
                            install_log,
                            f"INSTALL SKIPPED: {tool}",
                            f"No {pm} package available for {tool}",
                        )
                        progress.advance(task)
                        continue

                    progress.update(task, description=f"Installing {tool} ({info['desc']})")
                    _log_install_event(
                        install_log,
                        f"INSTALL START: {tool}",
                        f"package={pkg_name}, manager={pm}",
                    )
                    try:
                        success, output = install_system_tool(tool, pkg_name, pm, install_log)
                    except KeyboardInterrupt:
                        _log_install_event(install_log, "INSTALL INTERRUPTED", f"at tool {tool}")
                        console.print(
                            "\n[yellow] Installation interrupted. Re-run it later to continue.[/]"
                        )
                        status = {t: is_tool_installed(t) for t in TOOLS}
                        raise
                    status[tool] = success or is_tool_installed(tool)
                    if status[tool]:
                        _log_install_event(install_log, f"INSTALL SUCCESS: {tool}", output)
                    else:
                        _log_install_event(install_log, f"INSTALL FAILURE: {tool}", output)
                    progress.advance(task)

            # Summary after the progress bar exits
            installed_count = sum(1 for t, _ in missing if status.get(t))
            failed_count = sum(
                1 for t, _ in missing if not status.get(t) and t not in unavailable
            )
            already_count = len(TOOLS) - len(missing)
            console.print(
                f"\n[bold]Summary:[/] "
                f"[green]{installed_count} installed[/], "
                f"[red]{failed_count} failed[/], "
                f"[dim]{len(unavailable)} unavailable on this distro[/], "
                f"[dim]{already_count} already present[/]"
            )
            if unavailable:
                console.print(
                    f"[dim]Unavailable via {pm}: {', '.join(unavailable)}[/]"
                )
            console.print(f"[dim]Install log: {install_log}[/]\n")
        else:
            if not silent:
                console.print("[yellow] No supported package manager found." +
                              " Please install missing tools manually.[/]")
            _log_install_event(
                install_log,
                "NO PACKAGE MANAGER",
                "No supported package manager detected.",
            )

    # Install Python deps only when explicitly requested
    if install_python:
        _log_install_event(install_log, "PYTHON DEPS START", f"Count: {len(PYTHON_DEPS)}")
        install_python_deps(log_path=install_log)
        _log_install_event(install_log, "PYTHON DEPS END", "")

    remaining = sum(1 for v in status.values() if not v)
    _log_install_event(install_log, "INSTALL END", f"Missing tools remaining: {remaining}")
    return status


def show_tools_status() -> None:
    """Display a rich table of all tools and their install status."""
    table = Table(
        title="[bold red]NetReaper - Tools Status[/]",
        show_header=True, header_style="bold magenta"
    )
    table.add_column("Tool", style="cyan", width=20)
    table.add_column("Description", style="white", width=30)
    table.add_column("Status", justify="center", width=10)

    for tool, info in TOOLS.items():
        installed = is_tool_installed(tool)
        status_str = "[bold green] OK[/]" if installed else "[bold red] Missing[/]"
        table.add_row(tool, info["desc"], status_str)

    console.print(table)

    missing_count = sum(1 for t in TOOLS if not is_tool_installed(t))
    if missing_count > 0:
        console.print(f"\n[yellow] {missing_count} tools missing.[/]")
        if console.input("[cyan]Install missing tools now? [y/N]: [/]").lower() == "y":
            check_and_install_deps(silent=False)
    else:
        console.print("[bold green] All tools installed![/]")
