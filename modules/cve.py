"""
NetReaper - CVE lookup module
Author: 09azo14 | License: MIT
"""

import re
import json
import urllib.request
import urllib.error
import urllib.parse
import subprocess
from rich.console import Console

from core.config import get_config

console = Console()

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def parse_nmap_services(output: str) -> list:
    """Extract service/version strings from nmap -sV output."""
    services = []
    # Match lines like: 80/tcp open  http    Apache httpd 2.4.41
    pattern = re.compile(r"(\d+/\w+)\s+open\s+(\S+)\s+(.*)")
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            port = match.group(1)
            service = match.group(2)
            version = match.group(3).strip()
            services.append({
                "port": port,
                "service": service,
                "version": version,
                "query": f"{service} {version}".strip()
            })
    return services


def search_cve(query: str, results: int = 5) -> list:
    """Search CVEs via NIST NVD API for a given query."""
    safe_query = urllib.parse.quote(query, safe="")
    url = f"{NVD_API}?keywordSearch={safe_query}&resultsPerPage={results}"
    cves: list = []
    if not url.startswith(("http://", "https://")):
        console.print("[red] Refusing to open a non-HTTP CVE endpoint.[/]")
        return cves
    try:
        headers = {"User-Agent": "NetReaper/1.0.0"}
        api_key = get_config().get("nvd_api_key")
        if api_key:
            headers["apiKey"] = api_key
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310
            data = json.loads(response.read().decode("utf-8"))
            for item in data.get("vulnerabilities", [])[:results]:
                cve = item.get("cve", {})
                metrics = cve.get("metrics", {}).get("cvssMetricV31", [])
                cvss = metrics[0].get("cvssData", {}) if metrics else {}
                cves.append({
                    "id": cve.get("id", "N/A"),
                    "description": cve.get("descriptions", [{}])[0].get("value", "No description"),
                    "score": cvss.get("baseScore", "N/A"),
                    "severity": cvss.get("baseSeverity", "N/A"),
                })
    except urllib.error.URLError as e:
        console.print(f"[yellow] Could not contact NVD API (offline?): {e}[/]")
        console.print("[cyan]-> Trying offline fallback with searchsploit...[/]")
        try:
            is_cve = bool(re.match(r"CVE-\d{4}-\d+", query, re.IGNORECASE))
            cve_flag = "--cve" if is_cve else ""
            cmd = ["searchsploit", cve_flag, query] if cve_flag else ["searchsploit", query]
            cmd = [c for c in cmd if c]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.splitlines()[:results]:
                cves.append({
                    "id": line.strip(),
                    "description": "Offline result via searchsploit",
                    "score": "N/A",
                    "severity": "N/A",
                })
        except Exception as se:
            console.print(f"[yellow] Fallback searchsploit also failed: {se}[/]")
    except Exception as e:
        console.print(f"[yellow] CVE search error: {e}[/]")
    return cves


def run(action: str, target: str, logger) -> None:
    """Run CVE lookup."""
    if action == "from_nmap":
        # Find latest nmap report in current session
        nmap_output = ""
        for entry in logger.commands:
            if entry.get("module") in ("nmap_scan", "recon"):
                nmap_output = entry.get("output", "")
                break
        if not nmap_output:
            console.print("[yellow] No nmap scan found in this session.[/]")
            return

        services = parse_nmap_services(nmap_output)
        if not services:
            console.print("[yellow] No service/version detected in nmap output.[/]")
            return

        console.print(f"[bold cyan]-> Searching CVEs for {len(services)} services...[/]")
        report_lines = []
        for svc in services:
            console.print(f"[white]Service:[/] {svc['service']} {svc['version']} ({svc['port']})")
            cves = search_cve(svc["query"])
            if cves:
                report_lines.append(f"{svc['service']} {svc['version']} ({svc['port']}):")
                for cve in cves:
                    line = (
                        f"  - {cve['id']} | Score: {cve['score']} "
                        f"({cve['severity']}) | {cve['description'][:120]}"
                    )
                    console.print(line)
                    report_lines.append(line)
            else:
                console.print("[dim]  No CVEs found.[/]")
        if report_lines:
            logger.save_report(f"cve_lookup_{target}", "\n".join(report_lines))
    else:
        query = console.input("[cyan]Service/version to search: [/]")
        cves = search_cve(query)
        if not cves:
            console.print("[yellow] No CVEs found.[/]")
            return
        for cve in cves:
            console.print(f"[bold]{cve['id']}[/] Score: {cve['score']} ({cve['severity']})")
            console.print(f"[dim]{cve['description'][:200]}[/]")
