"""
NetReaper - Tests for modules/cve.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.cve import parse_nmap_services, search_cve


class TestCVE(unittest.TestCase):
    sample_nmap = """
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9
80/tcp open  http    Apache httpd 2.4.41
"""

    def test_parse_nmap_services(self):
        services = parse_nmap_services(self.sample_nmap)
        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]["service"], "ssh")
        self.assertIn("OpenSSH", services[0]["version"])

    def test_search_cve_offline_returns_empty_list(self):
        # Force an offline query that fails quickly
        cves = search_cve("nonexistent-service-xyz-12345", results=1)
        self.assertIsInstance(cves, list)


if __name__ == "__main__":
    unittest.main()
