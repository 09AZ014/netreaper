"""
NetReaper - Common output parsers
Author: 09azo14 | License: MIT
"""

import re


def extract_ports(output: str) -> list:
    """Extract open ports from nmap output."""
    ports = set()
    for line in output.splitlines():
        match = re.search(r"(\d+)/(\w+)\s+open", line)
        if match:
            ports.add(f"{match.group(2)}/{match.group(1)}")
    return sorted(ports)


def extract_services(output: str) -> list:
    """Extract service/version strings from nmap output."""
    services = set()
    for line in output.splitlines():
        match = re.search(r"\d+/\w+\s+open\s+(\S+)\s+(.*)", line)
        if match:
            services.add(f"{match.group(1)} {match.group(2)}".strip())
    return sorted(services)


def extract_os(output: str) -> str:
    """Extract OS guess from nmap output."""
    for line in output.splitlines():
        if "OS details:" in line:
            return line.split("OS details:", 1)[-1].strip()
        if "Running:" in line:
            return line.split("Running:", 1)[-1].strip()
    return ""
