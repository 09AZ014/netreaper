"""
NetReaper - Session logger and report generator
Author: 09azo14 | License: MIT
"""

import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()
REPORTS_DIR = Path(__file__).parent.parent / "reports"


class SessionLogger:
    """Handles logging of all commands and outputs."""

    def __init__(self):
        self.session_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = REPORTS_DIR / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.session_dir / "session.log"
        self.commands = []
        self.command_history = []
        self._write_header()

    def _write_header(self):
        with open(self.log_file, "w") as f:
            f.write("NetReaper v1.0.0 - Session Log\n")
            f.write("Author: 09azo14 | License: MIT\n")
            f.write(f"Session: {self.session_id}\n")
            f.write("=" * 60 + "\n\n")

    def log_command(self, module: str, command: str, output: str, target: str = ""):
        """Log a command execution."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "module": module,
            "target": target,
            "command": command,
            "output": output,
        }
        self.commands.append(entry)
        self.command_history.append(command)
        # Keep only last 50 commands
        if len(self.command_history) > 50:
            self.command_history = self.command_history[-50:]

        with open(self.log_file, "a") as f:
            f.write(f"[{entry['timestamp']}] MODULE={module} TARGET={target}\n")
            f.write(f"CMD: {command}\n")
            f.write(f"OUTPUT:\n{output}\n")
            f.write("-" * 60 + "\n")

    def save_report(self, name: str, content: str, fmt: str = "txt"):
        """Save a module report."""
        path = self.session_dir / f"{name}.{fmt}"
        with open(path, "w") as f:
            f.write(content)
        console.print(f"[green] Report saved: {path}[/]")
        return path

    def save_html_report(self, name: str, title: str, body: str):
        """Save an HTML report."""
        html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>{title} - NetReaper</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #111; color: #eee; padding: 20px; }}
        h1 {{ color: #ff3333; }}
        pre {{ background: #222; padding: 10px; overflow-x: auto; }}
        footer {{ margin-top: 40px; color: #666; font-size: 0.8em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Session:</strong> {self.session_id}</p>
    <p><strong>Timestamp:</strong> {datetime.datetime.now().isoformat()}</p>
    <hr>
    <pre>{body}</pre>
    <footer>NetReaper v1.0.0 - Author: 09azo14 | License: MIT</footer>
</body>
</html>"""
        path = self.session_dir / f"{name}.html"
        with open(path, "w") as f:
            f.write(html)
        return path

    def export_pdf(self):
        """Export a consolidated PDF report of the session."""
        try:
            from fpdf import FPDF
        except ImportError:
            console.print("[yellow]fpdf2 not installed. Cannot export PDF.[/]")
            return None

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "NetReaper Session Report", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Session: {self.session_id}", ln=True)
        pdf.cell(0, 10, "Author: 09azo14 | License: MIT", ln=True)
        pdf.ln(5)

        for entry in self.commands:
            pdf.set_font("Arial", "B", 11)
            ts = entry['timestamp'].encode('latin-1', 'ignore').decode('latin-1')
            mod = entry['module'].encode('latin-1', 'ignore').decode('latin-1')
            tgt = entry['target'].encode('latin-1', 'ignore').decode('latin-1')
            pdf.cell(0, 8, f"[{ts}] {mod} - {tgt}", ln=True)
            pdf.set_font("Courier", "", 9)
            for line in entry["output"].splitlines()[:50]:
                safe_line = line[:120].encode('latin-1', 'ignore').decode('latin-1')
                pdf.cell(0, 5, safe_line, ln=True)
            pdf.ln(2)

        pdf_path = self.session_dir / "consolidated_report.pdf"
        pdf.output(str(pdf_path))
        console.print(f"[green] PDF exported: {pdf_path}[/]")
        return pdf_path

    def list_reports(self):
        """Show all saved report sessions."""
        if not REPORTS_DIR.exists() or not any(REPORTS_DIR.iterdir()):
            console.print("[yellow]No reports found yet.[/]")
            return

        table = Table(title="[bold red]NetReaper - Reports[/]", header_style="bold magenta")
        table.add_column("Session", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Size")

        for session_dir in sorted(REPORTS_DIR.iterdir(), reverse=True):
            if session_dir.is_dir():
                files = list(session_dir.iterdir())
                size = sum(f.stat().st_size for f in files if f.is_file())
                table.add_row(
                    session_dir.name,
                    str(len(files)),
                    f"{size // 1024} KB",
                )
        console.print(table)

    def close(self):
        """Finalize the session log."""
        with open(self.log_file, "a") as f:
            f.write("\n[" + datetime.datetime.now().isoformat() + "] Session ended.\n")
