"""
NetReaper - Web application testing module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, select_wordlist, sanitize_for_shell
from core.platform import ensure_temp_dir

console = Console()


WEB_OPTIONS = {
    "gobuster": None,
    "ffuf": None,
    "sqlmap": None,
    "nikto": None,
    "headers": "curl -I -k http://{target}",
    "ssl": "sslscan --show-certificate {target}",
}


def run(action: str, target: str, logger) -> None:
    """Execute web testing command."""
    safe_target = sanitize_for_shell(target)
    temp_dir = ensure_temp_dir()
    if action == "gobuster":
        wordlist = sanitize_for_shell(select_wordlist())
        out_file = sanitize_for_shell(str(temp_dir / f"gobuster_{safe_target}.txt"))
        cmd = f"gobuster dir -u http://{safe_target} -w {wordlist} -o {out_file}"
    elif action == "ffuf":
        wordlist = sanitize_for_shell(select_wordlist())
        cmd = f"ffuf -u http://{safe_target}/FUZZ -w {wordlist}"
    elif action == "sqlmap":
        param = sanitize_for_shell(Prompt.ask("[cyan]GET parameter (e.g. id=1)[/]", default="id=1"))
        cmd = f"sqlmap -u 'http://{safe_target}/?{param}' --dbs --batch"
    elif action == "nikto":
        out_file = sanitize_for_shell(str(temp_dir / f"nikto_{safe_target}.html"))
        cmd = f"nikto -h http://{safe_target} -C all -o {out_file}"
    elif action == "headers":
        cmd = WEB_OPTIONS[action].format(target=safe_target)
    elif action == "ssl":
        cmd = WEB_OPTIONS[action].format(target=safe_target)
    else:
        console.print(f"[red] Unknown action: {action}[/]")
        return

    console.print(f"\n[bold cyan]-> Web: {action} on {target}[/]")
    output = run_command(cmd, logger=logger, module="web", target=target)
    logger.save_report(f"web_{action}_{target}", output)
