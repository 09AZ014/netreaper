"""
NetReaper - Scan diff module
Author: 09azo14 | License: MIT
"""

import difflib
from pathlib import Path
from rich.console import Console

console = Console()
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def list_reports():
    reports_dir = REPORTS_DIR
    reports = []
    text_exts = {".txt", ".log"}
    if reports_dir.exists():
        for session_dir in sorted(reports_dir.iterdir(), reverse=True):
            if session_dir.is_dir():
                for f in session_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in text_exts:
                        reports.append(str(f))
    return reports


def run(logger=None) -> None:
    """Compare two saved reports."""
    reports = list_reports()
    if len(reports) < 2:
        console.print("[yellow] At least two reports are needed to compare.[/]")
        return

    import questionary
    file_a = questionary.select("Base report:", choices=reports).ask()
    file_b = questionary.select("Report to compare:", choices=reports).ask()

    if not file_a or not file_b or file_a == file_b:
        console.print("[red] Select two different reports.[/]")
        return

    try:
        with open(file_a, "r") as fa, open(file_b, "r") as fb:
            lines_a = fa.readlines()
            lines_b = fb.readlines()
    except Exception as e:
        console.print(f"[red] Error reading files: {e}[/]")
        return

    diff = difflib.unified_diff(
        lines_a, lines_b,
        fromfile=file_a,
        tofile=file_b,
        lineterm=""
    )

    diff_output = "\n".join(diff)
    console.print("\n[bold cyan]== Scan Diff ==[/]")
    for line in diff_output.splitlines():
        if line.startswith("+"):
            console.print(f"[green]{line}[/]")
        elif line.startswith("-"):
            console.print(f"[red]{line}[/]")
        elif line.startswith("@@"):
            console.print(f"[yellow]{line}[/]")
        else:
            console.print(line)

    if logger:
        logger.save_report("scan_diff", diff_output)
