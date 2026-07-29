"""
NetReaper - Tests for core/parser.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.parser import extract_ports, extract_services, extract_os


class TestParser(unittest.TestCase):
    sample_nmap = """
Starting Nmap 7.94 ( https://nmap.org ) at 2024-01-01 00:00 UTC
Nmap scan report for 192.168.1.1
Host is up (0.0005s latency).
Not shown: 995 closed ports
PORT    STATE SERVICE
22/tcp  open  ssh     OpenSSH 8.9
80/tcp  open  http    Apache httpd 2.4.41
443/tcp open  https   nginx 1.18.0
MAC Address: 00:11:22:33:44:55 (Vendor)

OS details: Linux 5.4

Nmap done: 1 IP address (1 host up) scanned in 2.34 seconds
"""

    def test_extract_ports(self):
        ports = extract_ports(self.sample_nmap)
        self.assertIn("tcp/22", ports)
        self.assertIn("tcp/80", ports)
        self.assertIn("tcp/443", ports)

    def test_extract_services(self):
        services = extract_services(self.sample_nmap)
        self.assertTrue(any("ssh" in s for s in services))
        self.assertTrue(any("http" in s for s in services))

    def test_extract_os(self):
        os = extract_os(self.sample_nmap)
        self.assertIn("Linux 5.4", os)


if __name__ == "__main__":
    unittest.main()
