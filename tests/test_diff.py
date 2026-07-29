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

from modules import diff


class TestDiff(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.reports_dir = Path(self.tmpdir) / "reports"
        self.reports_dir.mkdir()
        # Patch the reports directory used by diff module
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


if __name__ == "__main__":
    unittest.main()
