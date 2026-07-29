"""
NetReaper - Dependency installer
Author: 09azo14 | License: MIT
"""

import os
import shutil
import subprocess
import sys
import threading
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

# All tools NetReaper can use
TOOLS = {
    "nmap":           {"apt": "nmap",                 "desc": "Network scanner"},
    "john":           {"apt": "john",                 "desc": "Password cracker"},
    "hashcat":        {"apt": "hashcat",              "desc": "GPU hash cracker"},
    "hydra":          {"apt": "hydra",                "desc": "Network brute forcer"},
    "tshark":         {"apt": "tshark",               "desc": "CLI Wireshark"},
    "tcpdump":        {"apt": "tcpdump",              "desc": "Packet analyzer"},
    "aircrack-ng":    {"apt": "aircrack-ng",          "desc": "WiFi cracker"},
    "wifite":         {"apt": "wifite",               "desc": "Auto WiFi attacker"},
    "nikto":          {"apt": "nikto",                "desc": "Web scanner"},
    "gobuster":       {"apt": "gobuster",             "desc": "Directory bruter"},
    "sqlmap":         {"apt": "sqlmap",               "desc": "SQL injection"},
    "searchsploit":   {"apt": "exploitdb",            "desc": "Exploit database"},
    "masscan":        {"apt": "masscan",              "desc": "Fast port scanner"},
    "arp-scan":       {"apt": "arp-scan",             "desc": "ARP network scanner"},
    "netdiscover":    {"apt": "netdiscover",          "desc": "Network discovery"},
    "sslscan":        {"apt": "sslscan",              "desc": "SSL/TLS scanner"},
    "enum4linux":     {"apt": "enum4linux",           "desc": "SMB enumeration"},
    "hping3":         {"apt": "hping3",               "desc": "Packet crafting"},
    "netcat":         {"apt": "netcat-openbsd",       "desc": "Network utility"},
    "ffuf":           {"apt": "ffuf",                 "desc": "Web fuzzer"},
    "wfuzz":          {"apt": "wfuzz",                "desc": "Web fuzzer"},
    "dirb":           {"apt": "dirb",                 "desc": "Web content scanner"},
    "lynis":          {"apt": "lynis",                "desc": "System auditor"},
    "fail2ban-client": {"apt": "fail2ban",             "desc": "Intrusion prevention"},
    "bettercap":      {"apt": "bettercap",            "desc": "Network attacker"},
    "ettercap":       {"apt": "ettercap-common",      "desc": "MITM tool"},
    "hashid":         {"apt": "hashid",               "desc": "Hash identifier"},
    "msfconsole":     {"apt": "metasploit-framework", "desc": "Exploit framework"},
    "wireshark":      {"apt": "wireshark",            "desc": "GUI packet analyzer"},
    "theHarvester":   {"apt": "theharvester",         "desc": "OSINT collector"},
    "smbclient":      {"apt": "smbclient",            "desc": "SMB client"},
    "responder":      {"apt": "responder",            "desc": "LLMNR/NBT-NS poisoner"},
    "crackmapexec":   {"apt": "crackmapexec",         "desc": "Active Directory/SMB tool"},
}

PYTHON_DEPS = [
    "rich", "questionary", "InquirerPy", "fpdf2", "colorama",
    "tabulate", "requests", "paramiko",
]


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


def get_os_specific_pkg_name(tool_name: str) -> str:
    """Return a package name that may differ per OS (Linux/macOS)."""
    os_type = get_os()
    darwin_map = {
        "john": "john-jumbo",
        "ettercap": "ettercap",
        "msfconsole": "metasploit",
    }
    if os_type == OS_MACOS and tool_name in darwin_map:
        return darwin_map[tool_name]
    return tool_name


def is_tool_installed(tool: str) -> bool:
    """Check if a CLI tool is installed."""
    return shutil.which(tool) is not None


def _is_root() -> bool:
    """Return True if the current process has root privileges."""
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _run_install_command(cmd: list, env: dict = None, timeout: int = 300) -> tuple:
    """
    Run an install command, stream output to console, and capture it.
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
            return 130, "\n".join(output_lines)
        finally:
            if timer is not None:
                timer.cancel()
        return returncode, "\n".join(output_lines)
    except Exception as exc:
        return -1, str(exc)


def install_system_tool(tool_name: str, pkg_name: str, pm: str) -> tuple:
    """Install a system tool using the platform-specific package manager."""
    os_type = get_os()
    try:
        if os_type == OS_WINDOWS:
            return install_windows_tool(tool_name)
        if os_type == OS_MACOS:
            return install_macos_tool(tool_name, pkg_name)

        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        env["APT_LISTCHANGES_FRONTEND"] = "none"

        sudo = [] if _is_root() else ["sudo"]
        sudo_env = [] if _is_root() else ["sudo", "-E"]

        if pm in ("apt", "apt-get"):
            cmd = sudo_env + [
                pm, "install", "-y",
                "-o", "DPkg::Lock::Timeout=300",
                "-o", "Dpkg::Options::=--force-confdef",
                "-o", "Dpkg::Options::=--force-confold",
                "--no-install-recommends",
                pkg_name,
            ]
        elif pm in ("yum", "dnf"):
            cmd = sudo + [pm, "install", "-y", pkg_name]
        elif pm == "pacman":
            cmd = sudo + ["pacman", "-S", "--noconfirm", pkg_name]
        elif pm == "zypper":
            cmd = sudo + ["zypper", "install", "-y", pkg_name]
        elif pm == "brew":
            cmd = ["brew", "install", pkg_name]
        else:
            return False, f"Unsupported package manager: {pm}"

        returncode, output = _run_install_command(cmd, env=env, timeout=360)
        return returncode == 0, _truncate_output(output)
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

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                if pm in ("apt", "apt-get"):
                    t = progress.add_task("Updating package lists", total=1)
                    env = os.environ.copy()
                    env["DEBIAN_FRONTEND"] = "noninteractive"
                    env["APT_LISTCHANGES_FRONTEND"] = "none"
                    sudo_prefix = [] if _is_root() else ["sudo", "-E"]
                    try:
                        result = subprocess.run(
                            sudo_prefix + [pm, "update", "-qq", "-o", "DPkg::Lock::Timeout=300"],
                            capture_output=True, text=True, timeout=300, env=env
                        )
                        _log_install_event(
                            install_log,
                            "PACKAGE LIST UPDATE",
                            f"returncode={result.returncode}\n{(result.stdout + result.stderr)[:1500]}",
                        )
                    except KeyboardInterrupt:
                        console.print("[yellow] Update interrupted; apt will release locks automatically.[/]")
                        _log_install_event(install_log, "PACKAGE LIST UPDATE", "Interrupted by user")
                        raise
                    except Exception as exc:
                        _log_install_event(install_log, "PACKAGE LIST UPDATE FAILED", str(exc))
                    progress.advance(t)

                task = progress.add_task("Installing system tools", total=len(missing))
                for tool, info in missing:
                    pkg_name = get_os_specific_pkg_name(tool)
                    progress.update(task, description=f"Installing {tool} ({info['desc']})")
                    _log_install_event(
                        install_log,
                        f"INSTALL START: {tool}",
                        f"package={pkg_name}, manager={pm}",
                    )
                    success, output = install_system_tool(tool, pkg_name, pm)
                    status[tool] = success
                    if success:
                        _log_install_event(
                            install_log,
                            f"INSTALL SUCCESS: {tool}",
                            output,
                        )
                    else:
                        _log_install_event(
                            install_log,
                            f"INSTALL FAILURE: {tool}",
                            output,
                        )
                    progress.advance(task)

            # Summary after progress bar exits
            installed_count = sum(1 for v in status.values() if v)
            failed_count = sum(1 for v in status.values() if not v)
            already_count = len(TOOLS) - len(missing)
            console.print(
                f"\n[bold]Summary:[/] "
                f"[green]{installed_count - already_count} installed[/], "
                f"[red]{failed_count} failed[/], "
                f"[dim]{already_count} already present[/]"
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

    _log_install_event(install_log, "INSTALL END", f"Missing tools remaining: {sum(1 for v in status.values() if not v)}")
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
