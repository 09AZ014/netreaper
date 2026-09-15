"""
NetReaper - Utility functions
Author: 09azo14 | License: MIT
"""

import subprocess
import shlex
from pathlib import Path
from rich.console import Console

from core.platform import (
    get_local_interfaces,
    get_default_gateway,
    get_local_ip,
    os_label,
    is_admin,
)
from core.config import get_config

console = Console()

_LEARNING_MODE = False


def set_learning_mode(enabled: bool):
    """Toggle global learning mode."""
    global _LEARNING_MODE
    _LEARNING_MODE = enabled


def get_learning_mode() -> bool:
    return _LEARNING_MODE


def sanitize_for_shell(value: str) -> str:
    """Basic shell escape for user input used in commands."""
    return shlex.quote(value)


def run_command(cmd: str, logger=None, module: str = "", target: str = "",
                timeout: int = None) -> str:
    """
    Run a shell command with real-time output streaming.
    Returns the full output as a string. When timeout is None the configured
    default command timeout is used.
    """
    if timeout is None:
        timeout = get_config().get_timeout("command")

    if get_learning_mode():
        from core.explanations import explain_command
        explain_command(cmd, console)
        import questionary
        if not questionary.confirm("Do you want to execute this command?").ask():
            console.print("[yellow] Command cancelled by user.[/]")
            return ""

    console.print(f"\n[bold yellow] Running:[/] [dim]{cmd}[/]\n")
    output_lines = []

    try:
        # The command string is assembled internally: tool names are constants and
        # every user-supplied value passes through sanitize_for_shell(). Several
        # modules require shell pipelines (see modules/defense.py), so shell=True
        # is intentional and cannot simply be disabled.
        proc = subprocess.Popen(
            cmd, shell=True,  # nosec B602
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )

        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                output_lines.append(line)
                # Color-code output
                if any(w in line.lower() for w in ["error", "failed", "denied"]):
                    console.print(f"[red]{line}[/]")
                elif any(w in line.lower() for w in ["open", "found", "success", "ok"]):
                    console.print(f"[green]{line}[/]")
                elif any(w in line.lower() for w in ["warning", "warn"]):
                    console.print(f"[yellow]{line}[/]")
                else:
                    console.print(line)

            proc.wait(timeout=timeout)

        except KeyboardInterrupt:
            proc.terminate()
            console.print("\n[yellow] Command cancelled by user.[/]")

    except Exception as e:
        console.print(f"[red] Error executing command: {e}[/]")

    full_output = "\n".join(output_lines)

    if logger:
        logger.log_command(module, cmd, full_output, target)

    return full_output


def build_command(base_cmd: str, **kwargs) -> str:
    """Build a shell command with quoted user inputs."""
    quoted = {k: sanitize_for_shell(v) for k, v in kwargs.items()}
    return base_cmd.format(**quoted)


def select_interface() -> str:
    """Prompt user to select a network interface."""
    import questionary
    interfaces = get_local_interfaces()
    if not interfaces:
        console.print("[red] No interface found.[/]")
        return ""
    configured = get_config().get("interface")
    default = configured if configured in interfaces else None
    return questionary.select(
        "Select network interface:",
        choices=interfaces,
        default=default,
    ).ask()


def select_wordlist() -> str:
    """
    Prompt user to select or enter a wordlist path.

    When a wordlist is configured and exists it is returned directly, so
    non-interactive and watch-mode runs never block on a prompt.
    """
    import questionary

    configured_file = get_config().get("wordlist")
    if configured_file and Path(configured_file).is_file():
        return str(configured_file)

    base_dir = Path(__file__).parent.parent / "wordlists"
    configured_dir = get_config().get("wordlist_dir")
    if configured_dir:
        base_dir = Path(configured_dir)
    built_in = [str(f) for f in base_dir.glob("*.txt")] if base_dir.exists() else []

    choices = built_in + ["Enter custom path"]
    selected = questionary.select("Select wordlist:", choices=choices).ask()

    if selected == "Enter custom path":
        return questionary.text("Wordlist path:").ask()
    return selected


def confirm_action(action: str) -> bool:
    """Confirm destructive or important actions."""
    import questionary
    return questionary.confirm(f"Are you sure you want to {action}?").ask()


def show_dashboard():
    """Show local network dashboard. OS-aware."""
    console.print("\n[bold cyan]== Session Dashboard ==[/]")
    try:
        ip = get_local_ip()
        gw = get_default_gateway()
        interfaces = get_local_interfaces()
        console.print(f"[white]Operating System:[/] {os_label()}")
        console.print(f"[white]Local IP:[/] {ip}")
        console.print(f"[white]Gateway:[/] {gw}")
        console.print(f"[white]Interfaces:[/] {', '.join(interfaces) if interfaces else 'N/A'}")
        if not is_admin():
            console.print("[yellow] No administrative privileges - some modules may fail.[/]")
    except Exception as e:
        console.print(f"[yellow] Could not obtain dashboard: {e}[/]")
