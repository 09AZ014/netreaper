"""
NetReaper - Tests for modules/diff.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import diff  # noqa: E402
from core import snapshot  # noqa: E402

BASE_HOSTS = {
    "192.168.1.10": [("22/tcp", "ssh OpenSSH 8.2"), ("80/tcp", "http Apache 2.4")],
}


def _nmap_report(hosts):
    """Build a minimal nmap-style report for the given host/port pairs."""
    lines = []
    for host, ports in hosts.items():
        lines.append(f"Nmap scan report for {host}")
        lines.append("Host is up (0.001s latency).")
        lines.append("PORT   STATE SERVICE VERSION")
        for port, service in ports:
            lines.append(f"{port} open  {service}")
        lines.append("")
    return "\n".join(lines)


class TestListReports(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.reports_dir = Path(self.tmpdir) / "reports"
        self.reports_dir.mkdir()
        self.orig_reports_dir = diff.REPORTS_DIR
        diff.REPORTS_DIR = self.reports_dir

    def tearDown(self):
        diff.REPORTS_DIR = self.orig_reports_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_list_reports_finds_text_files(self):
        session = self.reports_dir / "2024-01-01_00-00-00"
        session.mkdir()
        (session / "scan1.txt").write_text("22/tcp open")
        (session / "scan2.log").write_text("80/tcp open")
        (session / "report.pdf").write_text("binary")

        reports = diff.list_reports()
        self.assertEqual(len(reports), 2)
        self.assertTrue(any("scan1.txt" in r for r in reports))
        self.assertTrue(any("scan2.log" in r for r in reports))

    def test_list_reports_ignores_non_text(self):
        session = self.reports_dir / "2024-01-01_00-00-00"
        session.mkdir()
        (session / "report.pdf").write_text("binary")
        (session / "report.html").write_text("<html></html>")
        reports = diff.list_reports()
        self.assertEqual(len(reports), 0)

    def test_list_reports_missing_dir(self):
        diff.REPORTS_DIR = Path(self.tmpdir) / "does_not_exist"
        self.assertEqual(diff.list_reports(), [])


class TestDiffSnapshots(unittest.TestCase):
    def _base(self):
        return snapshot.build_snapshot(_nmap_report(BASE_HOSTS))

    def test_detects_new_host(self):
        base = self._base()
        new = snapshot.build_snapshot(
            _nmap_report({
                **BASE_HOSTS,
                "192.168.1.11": [("443/tcp", "ssl https")],
            })
        )
        result = diff.diff_snapshots(base, new)
        self.assertEqual(result["hosts_added"], ["192.168.1.11"])
        self.assertFalse(diff.is_empty_diff(result))

    def test_detects_removed_host(self):
        base = snapshot.build_snapshot(
            _nmap_report({
                "192.168.1.10": [("22/tcp", "ssh")],
                "192.168.1.11": [("443/tcp", "ssl")],
            })
        )
        new = self._base()
        result = diff.diff_snapshots(base, new)
        self.assertEqual(result["hosts_removed"], ["192.168.1.11"])

    def test_detects_port_opened_and_closed(self):
        base = self._base()
        new = snapshot.build_snapshot(
            _nmap_report({
                "192.168.1.10": [
                    ("22/tcp", "ssh OpenSSH 8.2"),
                    ("3306/tcp", "mysql MySQL 8.0"),
                ],
            })
        )
        result = diff.diff_snapshots(base, new)
        changes = result["hosts_changed"]["192.168.1.10"]
        self.assertEqual(changes["ports_added"], ["3306/tcp"])
        self.assertEqual(changes["ports_removed"], ["80/tcp"])

    def test_detects_service_version_change(self):
        base = self._base()
        new = snapshot.build_snapshot(
            _nmap_report({
                "192.168.1.10": [
                    ("22/tcp", "ssh OpenSSH 9.0"),
                    ("80/tcp", "http Apache 2.4"),
                ],
            })
        )
        result = diff.diff_snapshots(base, new)
        changed = result["hosts_changed"]["192.168.1.10"]["services_changed"]
        self.assertIn("22/tcp", changed)
        self.assertIn("OpenSSH 9.0", changed["22/tcp"]["to"])

    def test_detects_os_change(self):
        base = {"hosts": {"10.0.0.1": {"ports": {}, "services": {}, "os": "Linux 4.15", "mac": ""}}}
        new = {"hosts": {"10.0.0.1": {"ports": {}, "services": {}, "os": "Windows 10", "mac": ""}}}
        result = diff.diff_snapshots(base, new)
        self.assertEqual(
            result["hosts_changed"]["10.0.0.1"]["os_changed"],
            {"from": "Linux 4.15", "to": "Windows 10"},
        )

    def test_identical_snapshots_are_empty(self):
        base = self._base()
        result = diff.diff_snapshots(base, self._base())
        self.assertTrue(diff.is_empty_diff(result))

    def test_empty_snapshots_are_empty_diff(self):
        result = diff.diff_snapshots({"hosts": {}}, {"hosts": {}})
        self.assertTrue(diff.is_empty_diff(result))


class TestFormatting(unittest.TestCase):
    def test_no_changes_message(self):
        text = diff.format_semantic_diff(
            {"hosts_added": [], "hosts_removed": [], "hosts_changed": {}}
        )
        self.assertIn("No changes", text)

    def test_format_contains_markers(self):
        result = {
            "hosts_added": ["192.168.1.11"],
            "hosts_removed": [],
            "hosts_changed": {
                "192.168.1.10": {
                    "ports_added": ["3306/tcp"],
                    "ports_removed": [],
                    "services_changed": {"22/tcp": {"from": "ssh 8.2", "to": "ssh 9.0"}},
                }
            },
        }
        text = diff.format_semantic_diff(result)
        self.assertIn("[+] New host discovered: 192.168.1.11", text)
        self.assertIn("port opened: 3306/tcp", text)
        self.assertNotIn("ports_added", text)
        self.assertIn("service 22/tcp: ssh 8.2 -> ssh 9.0", text)


class TestCompare(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dir = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_compare_uses_semantic_diff(self):
        a = self.dir / "a.txt"
        b = self.dir / "b.txt"
        a.write_text(_nmap_report({"192.168.1.10": [("22/tcp", "ssh OpenSSH 8.2")]}))
        b.write_text(_nmap_report({
            "192.168.1.10": [("22/tcp", "ssh OpenSSH 8.2")],
            "192.168.1.11": [("80/tcp", "http Apache 2.4")],
        }))
        output = diff.compare(str(a), str(b))
        self.assertIn("New host discovered: 192.168.1.11", output)

    def test_compare_falls_back_to_text_diff(self):
        a = self.dir / "a.txt"
        b = self.dir / "b.txt"
        a.write_text("plain line one\n")
        b.write_text("plain line two\n")
        output = diff.compare(str(a), str(b))
        self.assertIn("-plain line one", output)
        self.assertIn("+plain line two", output)

    def test_build_snapshot_from_unreadable_path(self):
        snap = diff.build_snapshot_from_report(str(self.dir))
        self.assertEqual(snap, {"hosts": {}})


class TestRenderingAndRun(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.reports_dir = Path(self.tmpdir) / "reports"
        self.reports_dir.mkdir()
        self.orig_reports_dir = diff.REPORTS_DIR
        diff.REPORTS_DIR = self.reports_dir

    def tearDown(self):
        diff.REPORTS_DIR = self.orig_reports_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_print_semantic_does_not_raise(self):
        result = {
            "hosts_added": ["10.0.0.2"],
            "hosts_removed": ["10.0.0.1"],
            "hosts_changed": {
                "10.0.0.3": {
                    "ports_added": ["22/tcp"],
                    "ports_removed": ["80/tcp"],
                    "services_changed": {"22/tcp": {"from": "ssh 8", "to": "ssh 9"}},
                    "os_changed": {"from": "Linux", "to": "Windows"},
                }
            },
        }
        diff._print_semantic(result)
        diff._print_semantic({"hosts_added": [], "hosts_removed": [], "hosts_changed": {}})

    def test_print_text_diff_does_not_raise(self):
        diff._print_text_diff("+added\n-removed\n@@ hunk\n context")

    def test_run_requires_two_reports(self):
        diff.run()


if __name__ == "__main__":
    unittest.main()
