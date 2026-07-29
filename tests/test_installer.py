"""
NetReaper - Unit tests for installer module
Author: 09azo14 | License: MIT
"""

import unittest
from pathlib import Path
from unittest import mock

from core import installer


class TestInstallerLogging(unittest.TestCase):
    """Tests for install event logging."""

    def test_get_install_log_path_creates_logs_dir(self):
        """Install log path should reside under logs/ directory."""
        log_path = installer.get_install_log_path()
        self.assertTrue(str(log_path).startswith(str(installer.INSTALL_LOG_DIR)))
        self.assertTrue(log_path.name.startswith("install_"))
        self.assertEqual(log_path.suffix, ".log")

    def test_log_install_event_writes_entry(self):
        """_log_install_event should append a timestamped event."""
        log_file = installer.INSTALL_LOG_DIR / "test_install_event.log"
        log_file.write_text("", encoding="utf-8")
        try:
            installer._log_install_event(log_file, "TEST EVENT", "details line")
            content = log_file.read_text(encoding="utf-8")
            self.assertIn("TEST EVENT", content)
            self.assertIn("details line", content)
        finally:
            log_file.unlink(missing_ok=True)

    def test_log_install_event_timestamp_and_indentation(self):
        """_log_install_event should timestamp and indent multi-line details."""
        log_file = installer.INSTALL_LOG_DIR / "test_format.log"
        log_file.write_text("", encoding="utf-8")
        try:
            installer._log_install_event(log_file, "FORMAT EVENT", "line1\nline2")
            content = log_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            self.assertEqual(len(lines), 3)
            self.assertIn("FORMAT EVENT", lines[0])
            self.assertTrue(lines[1].startswith("    "))
            self.assertTrue(lines[2].startswith("    "))
        finally:
            log_file.unlink(missing_ok=True)

    def test_log_install_event_no_op_for_none(self):
        """_log_install_event should not raise when log_path is None."""
        installer._log_install_event(None, "EVENT", "details")

    def test_truncate_output_combines_and_limits(self):
        """_truncate_output should combine stdout/stderr and respect the limit."""
        result = installer._truncate_output("stdout ", "stderr", limit=10)
        self.assertEqual(result, "stdout std")
        self.assertEqual(len(result), 10)

    def test_install_system_tool_returns_tuple(self):
        """install_system_tool should return a (bool, str) tuple."""
        # Unknown package manager path returns (False, "...")
        result = installer.install_system_tool("nmap", "nmap", "unknown_pm")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_install_windows_tool_returns_tuple(self):
        """install_windows_tool should return a (bool, str) tuple."""
        with mock.patch("shutil.which", return_value=None):
            result = installer.install_windows_tool("nmap")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_install_macos_tool_returns_tuple(self):
        """install_macos_tool should return a (bool, str) tuple."""
        with mock.patch("shutil.which", return_value=None):
            result = installer.install_macos_tool("nmap", "nmap")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertFalse(result[0])


if __name__ == "__main__":
    unittest.main()
