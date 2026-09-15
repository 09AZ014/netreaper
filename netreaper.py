#!/usr/bin/env python3
"""
NetReaper v1.0.0 - Pentest & Security CLI Tool
Author: 09azo14
License: MIT License
GitHub: github.com/09azo14/netreaper

MIT License
Copyright (c) 2024 09azo14
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_project_venv_python(project_root=None):
    roots = []
    if project_root is not None:
        roots.append(Path(project_root).resolve())
    else:
        script_dir = Path(__file__).resolve().parent
        roots.extend([script_dir, script_dir.parent])

    for root in roots:
        candidates = (
            root / ".venv" / "bin" / "python",
            root / ".venv" / "Scripts" / "python.exe",
            root / ".venv" / "Scripts" / "python",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate

    return roots[0] / ".venv" / "bin" / "python"


def ensure_project_python():
    project_root = Path(__file__).resolve().parent
    venv_python = get_project_venv_python(project_root)
    venv_prefix = venv_python.parent.parent if venv_python != Path(".") else None

    if not venv_python.exists():
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(project_root / ".venv")],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return

    if venv_prefix is not None:
        current_prefix = Path(sys.prefix).resolve()
        if current_prefix != venv_prefix.resolve():
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)


VERSION = "1.0.0"

# Non-interactive commands and the module mapping that backs each one.
CLI_COMMANDS = {
    "recon": ("modules.recon", "SCAN_OPTIONS", "reconnaissance action"),
    "web": ("modules.web", "WEB_OPTIONS", "web application testing action"),
    "vuln": ("modules.vuln", "VULN_SCANS", "vulnerability scanning action"),
}


def parse_args(argv=None):
    desc = f"NetReaper v{VERSION} - Pentest & Security CLI Tool (by 09azo14, MIT License)"
    parser = argparse.ArgumentParser(prog="netreaper", description=desc)
    parser.add_argument("--version", action="version", version=f"NetReaper {VERSION}")
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick scan: ping sweep + top ports without menu"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Quiet mode: no banner, only output"
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update NetReaper via git pull and refresh tools"
    )
    parser.add_argument(
        "--target", type=str, default=None,
        help="Target host or range (defaults to the value in the config file)"
    )
    parser.add_argument(
        "--learn", action="store_true",
        help="Enable learning mode (explain commands before running)"
    )
    parser.add_argument(
        "--list", dest="list_actions", action="store_true",
        help="List available module actions and exit"
    )
    parser.add_argument(
        "--install", action="store_true",
        help="Check and install missing tools before running"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="{recon,web,vuln,watch}")
    for name, (_, _, action_help) in CLI_COMMANDS.items():
        sub = subparsers.add_parser(name, help=f"Run a {action_help}")
        sub.add_argument("action", nargs="?", help=f"{name} action to run")
        # SUPPRESS keeps the top-level --target/--install values when absent.
        sub.add_argument("-t", "--target", default=argparse.SUPPRESS)
        sub.add_argument("--install", action="store_true", default=argparse.SUPPRESS)

    watch_parser = subparsers.add_parser(
        "watch", help="Re-run a scan and alert when the results change"
    )
    watch_parser.add_argument(
        "--module", choices=["recon", "nmap", "web", "vuln"], default="recon"
    )
    watch_parser.add_argument("--action", required=True, help="Action to watch")
    watch_parser.add_argument("-t", "--target", default=argparse.SUPPRESS)
    watch_parser.add_argument(
        "--interval", type=int, default=None, help="Seconds between runs"
    )
    watch_parser.add_argument(
        "--count", type=int, default=0,
        help="Stop after N runs (0 = run until interrupted)"
    )
    watch_parser.add_argument(
        "--webhook", default=None, help="POST change alerts to this URL as JSON"
    )

    return parser.parse_args(argv)


def available_actions(command: str) -> list:
    """Return the sorted action names supported by a CLI command."""
    import importlib

    module_name, mapping_name, _ = CLI_COMMANDS[command]
    module = importlib.import_module(module_name)
    return sorted(getattr(module, mapping_name).keys())


def watch_available_actions(command: str) -> list:
    """Return the actions that watch mode can run for a module."""
    from core import watch
    return watch.available_actions(command)


def print_available_actions() -> None:
    """Print every non-interactive action with usage examples."""
    print("\nNetReaper module actions:")
    for command in CLI_COMMANDS:
        print(f"\n  {command}:")
        for action in available_actions(command):
            print(f"    - {action}")

    print("\nWatch mode (netreaper watch --module <module> --action <action>):")
    for command in ("recon", "nmap", "web", "vuln"):
        print(f"\n  {command}:")
        for action in watch_available_actions(command):
            print(f"    - {action}")

    print("\nUsage: netreaper <command> <action> --target <host>")
    print("Example: netreaper recon ping_sweep --target 192.168.1.0/24")
    print("Example: netreaper watch --module recon --action ping_sweep -t 192.168.1.0/24")
    print("Example: netreaper watch --module vuln --action nmap_vuln -t 192.168.1.10\n")


def resolve_target(args) -> str:
    """Resolve the target from the CLI flags or the saved configuration."""
    if getattr(args, "target", None):
        return args.target
    from core.config import get_config
    return get_config().get("target") or ""


def run_cli_command(args, logger=None) -> int:
    """Run a single module action without entering the interactive menu."""
    from core.logger import SessionLogger
    from core.profile import TargetProfile

    if not args.action:
        print(f"[!] Missing {args.command} action. Use --list to see the options.")
        return 2

    valid = available_actions(args.command)
    if args.action not in valid:
        print(f"[!] Unknown {args.command} action: {args.action}")
        print(f"    Available: {', '.join(valid)}")
        return 2

    target = resolve_target(args)
    if not target:
        print("[!] No target given. Pass --target or set 'target' in the config file.")
        return 2

    if logger is None:
        logger = SessionLogger()

    try:
        if args.command == "recon":
            from modules import recon
            recon.run(args.action, target, logger, TargetProfile())
        elif args.command == "web":
            from modules import web
            web.run(args.action, target, logger)
        elif args.command == "vuln":
            from modules import vuln
            vuln.run(args.action, target, logger)
    except EOFError:
        print("[!] This action needs interactive input. Run NetReaper without"
              " arguments to use the menu, or choose a non-interactive action.")
        return 2

    return 0


def run_watch_command(args) -> int:
    """Start watch mode from the non-interactive CLI."""
    from core import watch
    from core.logger import SessionLogger
    from core.profile import TargetProfile

    valid = watch.available_actions(args.module)
    if args.action not in valid:
        print(f"[!] Unknown {args.module} action: {args.action}")
        print(f"    Available: {', '.join(valid)}")
        return 2

    target = resolve_target(args)
    if not target:
        print("[!] No target given. Pass --target or set 'target' in the config file.")
        return 2

    logger = SessionLogger()
    try:
        watch.run(
            args.module, args.action, target, logger,
            interval=args.interval, max_iterations=args.count,
            webhook=args.webhook, profile=TargetProfile(),
        )
    except EOFError:
        print("[!] This action asks for input on every run. Configure the relevant"
              " value (for example 'wordlist') or choose a non-interactive action.")
        return 2
    finally:
        logger.close()
    return 0


def quick_scan(target):
    from core.logger import SessionLogger
    from modules import nmap_scan

    logger = SessionLogger()
    print(f"\n[NetReaper] Quick scan on {target}\n")
    nmap_scan.run("ping_sweep", target, logger)
    nmap_scan.run("fast_ports", target, logger)


def main():
    ensure_project_python()

    from core.banner import show_banner
    from core.installer import check_and_install_deps
    from core.menu import MainMenu
    from core.utils import run_command, set_learning_mode
    from core.config import get_config

    args = parse_args()

    if args.update:
        print("\n[NetReaper] Updating via git pull...\n")
        run_command("git pull", module="update")
        check_and_install_deps(silent=False)
        return

    if args.list_actions:
        print_available_actions()
        return

    if args.command:
        if args.learn:
            set_learning_mode(True)
        if args.install:
            check_and_install_deps(silent=False)
        if args.command == "watch":
            sys.exit(run_watch_command(args))
        sys.exit(run_cli_command(args))

    if args.quick:
        target = args.target or get_config().get("target") or "192.168.1.0/24"
        if not args.quiet:
            show_banner()
        quick_scan(target)
        return

    try:
        if not args.quiet:
            show_banner()
        if args.learn:
            set_learning_mode(True)
        check_and_install_deps(silent=True, install_python=False)
        menu = MainMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted. Exiting NetReaper...\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
