"""
NetReaper — Banner and intro display
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import time

console = Console()

BANNER = r"""
 ███▄    █ ▓█████▄▄▄█████▓    ██▀███  ▓█████ ▄▄▄       ██▓███  ▓█████  ██▀███
 ██ ▀█   █ ▓█   ▀▓  ██▒ ▓▒   ▓██ ▒ ██▒▓█   ▒████▄    ▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▓██  ▀█ ██▒▒███  ▒ ▓██░ ▒░   ▓██ ░▄█ ▒▒███  ▒██  ▀█▄  ▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▓██▒  ▐▌██▒▒▓█  ▄░ ▓██▓ ░    ▒██▀▀█▄  ▒▓█  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▓█  ▄ ▒██▀▀█▄
██░   ▓██░░▒████▒ ▒██▒ ░    ░██▓ ▒██▒░▒████▒▓█   ▓██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ▒░   ▒ ▒ ░░ ▒░ ░ ▒ ░░      ░ ▒▓ ░▒▓░░░ ▒░ ░▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
"""


def show_banner():
    """Display the NetReaper banner."""
    console.clear()
    console.print(BANNER, style="bold red")
    console.print(
        Panel(
            Align.center(
                "[bold white]v1.0.0[/] — [bold red]Pentest & Security CLI Tool[/]\n"
                "[dim]Author: [bold cyan]09azo14[/] | License: [bold green]MIT[/] | "
                "For authorized testing only[/]"
            ),
            border_style="red",
        )
    )
    time.sleep(0.5)
