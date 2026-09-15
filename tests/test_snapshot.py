"""
NetReaper - Tests for core/snapshot.py
Author: 09azo14 | License: MIT
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import snapshot  # noqa: E402

NMAP_OUTPUT = """\
# Nmap 7.94 scan initiated Mon Jan  1 00:00:00 2024 as: nmap -sV 192.168.1.10
Nmap scan report for router.local (192.168.1.1)
Host is up (0.0012s latency).
Not shown: 997 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5
80/tcp open  http    Apache httpd 2.4.41
MAC Address: AA:BB:CC:DD:EE:FF (TP-LINK TECHNOLOGIES)
OS details: Linux 4.15 - 5.6

Nmap scan report for 192.168.1.20
Host is up (0.0034s latency).
PORT     STATE SERVICE VERSION
443/tcp  open  ssl/https
"""

ARP_OUTPUT = """\
Interface: enp4s0, type: EN10MB, MAC: 00:11:22:33:44:55
Starting arp-scan 1.10.0 with 256 hosts
192.168.1.1      aa:bb:cc:dd:ee:ff       TP-LINK TECHNOLOGIES CO.,LTD
192.168.1.50     11:22:33:44:55:66       (Unknown)
3 packets received by filter
"""

MASSCAN_OUTPUT = """\
Discovered open port 80/tcp on 192.168.1.30
Discovered open port 22/tcp on 192.168.1.30
"""


class TestParseNmap(unittest.TestCase):
    def test_extracts_hosts_by_ip(self):
        hosts = snapshot.parse_nmap(NMAP_OUTPUT)
        self.assertIn("192.168.1.1", hosts)
        self.assertIn("192.168.1.20", hosts)

    def test_extracts_ports_and_services(self):
        hosts = snapshot.parse_nmap(NMAP_OUTPUT)
        self.assertEqual(set(hosts["192.168.1.1"]["ports"]), {"22/tcp", "80/tcp"})
        self.assertIn("OpenSSH", hosts["192.168.1.1"]["services"]["22/tcp"])

    def test_extracts_mac_and_os(self):
        hosts = snapshot.parse_nmap(NMAP_OUTPUT)
        self.assertEqual(hosts["192.168.1.1"]["mac"], "aa:bb:cc:dd:ee:ff")
        self.assertIn("Linux", hosts["192.168.1.1"]["os"])

    def test_ignores_unrelated_output(self):
        self.assertEqual(snapshot.parse_nmap("no hosts here"), {})


class TestParseArpScan(unittest.TestCase):
    def test_extracts_ip_and_mac(self):
        hosts = snapshot.parse_arp_scan(ARP_OUTPUT)
        self.assertEqual(hosts["192.168.1.1"]["mac"], "aa:bb:cc:dd:ee:ff")
        self.assertEqual(hosts["192.168.1.50"]["mac"], "11:22:33:44:55:66")

    def test_ignores_header_lines(self):
        hosts = snapshot.parse_arp_scan(ARP_OUTPUT)
        self.assertEqual(len(hosts), 2)


class TestParseMasscan(unittest.TestCase):
    def test_extracts_open_ports(self):
        hosts = snapshot.parse_masscan(MASSCAN_OUTPUT)
        self.assertEqual(set(hosts["192.168.1.30"]["ports"]), {"80/tcp", "22/tcp"})


class TestBuildSnapshot(unittest.TestCase):
    def test_merges_parsers(self):
        combined = NMAP_OUTPUT + "\n" + ARP_OUTPUT + "\n" + MASSCAN_OUTPUT
        snap = snapshot.build_snapshot(combined)
        hosts = snap["hosts"]
        self.assertIn("192.168.1.1", hosts)
        self.assertIn("192.168.1.50", hosts)
        self.assertIn("192.168.1.30", hosts)

    def test_empty_input_returns_no_hosts(self):
        self.assertFalse(snapshot.has_hosts(snapshot.build_snapshot("")))

    def test_has_hosts_true_when_parsed(self):
        self.assertTrue(snapshot.has_hosts(snapshot.build_snapshot(NMAP_OUTPUT)))

    def test_none_input_is_handled(self):
        self.assertFalse(snapshot.has_hosts(snapshot.build_snapshot(None)))


class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_to_json_roundtrip(self):
        snap = snapshot.build_snapshot(NMAP_OUTPUT)
        restored = json.loads(snapshot.to_json(snap))
        self.assertEqual(
            restored["hosts"]["192.168.1.1"]["ports"],
            snap["hosts"]["192.168.1.1"]["ports"],
        )

    def test_save_and_load_snapshot(self):
        snap = snapshot.build_snapshot(NMAP_OUTPUT)
        path = Path(self.tmpdir) / "nested" / "snap.json"
        returned = snapshot.save_snapshot(snap, path)
        self.assertTrue(returned.exists())
        self.assertEqual(snapshot.load_snapshot(returned)["hosts"], snap["hosts"])


if __name__ == "__main__":
    unittest.main()
