"""
NetReaper - Password cracking and brute force module
Author: 09azo14 | License: MIT
"""

from rich.console import Console
from rich.prompt import Prompt
from core.utils import run_command, select_wordlist, sanitize_for_shell

console = Console()


def run(mode: str, logger) -> None:
    """Run password cracking or brute force."""
    if mode == "john":
        hash_file = sanitize_for_shell(Prompt.ask("[cyan]Hash file[/]"))
        wordlist = sanitize_for_shell(select_wordlist())
        cmd = f"john --format=auto {hash_file} --wordlist={wordlist}"
        output = run_command(cmd, logger=logger, module="crack", target=hash_file)
        logger.save_report("crack_john", output)
    elif mode == "hashcat":
        hash_file = sanitize_for_shell(Prompt.ask("[cyan]Hash file[/]"))
        mode_num = sanitize_for_shell(Prompt.ask("[cyan]Hashcat mode (-m)[/]", default="0"))
        wordlist = sanitize_for_shell(select_wordlist())
        cmd = f"hashcat -m {mode_num} {hash_file} {wordlist} --force"
        output = run_command(cmd, logger=logger, module="crack", target=hash_file)
        logger.save_report("crack_hashcat", output)
    elif mode == "hashid":
        hash_string = sanitize_for_shell(Prompt.ask("[cyan]Hash string[/]"))
        cmd = f"hashid {hash_string}"
        output = run_command(cmd, logger=logger, module="crack", target=hash_string)
        logger.save_report("crack_hashid", output)
    else:
        brute_services(logger, mode)


def brute_services(logger, mode: str) -> None:
    target = sanitize_for_shell(Prompt.ask("[cyan]Target (IP/Domain)[/]", default="192.168.1.1"))
    user = sanitize_for_shell(Prompt.ask("[cyan]Username[/]", default="admin"))
    wordlist = sanitize_for_shell(select_wordlist())

    if mode == "brute_http":
        path = sanitize_for_shell(Prompt.ask("[cyan]Path (e.g. /login)[/]", default="/"))
        cmd = f"hydra -l {user} -P {wordlist} http-get://{target}{path}"
    elif mode == "brute_router":
        cmd = f"hydra -l {user} -P {wordlist} http-form-post://{target}/login.cgi:'user=^USER^&pass=^PASS^':F=incorrect"
    elif mode == "brute_ssh":
        cmd = f"hydra -l {user} -P {wordlist} ssh://{target}"
    elif mode == "brute_ftp":
        cmd = f"hydra -l {user} -P {wordlist} ftp://{target}"
    elif mode == "brute_smb":
        cmd = f"hydra -l {user} -P {wordlist} smb://{target}"
    elif mode == "brute_db":
        cmd = f"hydra -l {user} -P {wordlist} mysql://{target}"
    else:
        console.print(f"[red] Unknown mode: {mode}[/]")
        return

    output = run_command(cmd, logger=logger, module="crack", target=target)
    logger.save_report(f"crack_{mode}_{target}", output)
