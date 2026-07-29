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


def parse_args():
    desc = "NetReaper v1.0.0 - Pentest & Security CLI Tool (by 09azo14, MIT License)"
    parser = argparse.ArgumentParser(prog="netreaper", description=desc)
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
        "--target", type=str, default="192.168.1.0/24",
        help="Target for quick scan"
    )
    parser.add_argument(
        "--learn", action="store_true",
        help="Enable learning mode (explain commands before running)"
    )
    return parser.parse_args()


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

    args = parse_args()

    if args.update:
        print("\n[NetReaper] Updating via git pull...\n")
        run_command("git pull", module="update")
        check_and_install_deps(silent=False)
        return

    if args.quick:
        if not args.quiet:
            show_banner()
        quick_scan(args.target)
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
