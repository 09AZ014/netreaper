"""
NetReaper - Unit tests for installer module
Author: 09azo14 | License: MIT
"""

import unittest
from unittest import mock

from core import installer


def _next_output(outputs):
    """Return a side effect that yields the next mocked install output."""
    return lambda *a, **k: next(outputs)


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


class TestPackageNameMapping(unittest.TestCase):
    """Distro-specific package name resolution."""

    def test_normalizes_package_manager_alias(self):
        self.assertEqual(installer._normalize_pm("apt-get"), "apt")
        self.assertEqual(installer._normalize_pm("yum"), "dnf")
        self.assertEqual(installer._normalize_pm("pacman"), "pacman")

    def test_uses_apt_name_for_searchsploit(self):
        """searchsploit ships in the exploitdb package, not a package of that name."""
        self.assertEqual(installer.get_os_specific_pkg_name("searchsploit", "apt"), "exploitdb")
        self.assertEqual(installer.get_os_specific_pkg_name("searchsploit", "apt-get"), "exploitdb")

    def test_uses_manager_specific_override(self):
        self.assertEqual(installer.get_os_specific_pkg_name("tshark", "dnf"), "wireshark-cli")
        self.assertEqual(installer.get_os_specific_pkg_name("tshark", "pacman"), "wireshark-cli")
        self.assertEqual(installer.get_os_specific_pkg_name("netcat", "dnf"), "nmap-ncat")
        self.assertEqual(installer.get_os_specific_pkg_name("netcat", "pacman"), "openbsd-netcat")
        self.assertEqual(installer.get_os_specific_pkg_name("ettercap", "apt"), "ettercap-common")

    def test_yum_alias_resolves_to_dnf_name(self):
        self.assertEqual(installer.get_os_specific_pkg_name("tshark", "yum"), "wireshark-cli")

    def test_returns_none_when_unavailable(self):
        """Tools absent from a distribution's repositories resolve to None."""
        self.assertIsNone(installer.get_os_specific_pkg_name("msfconsole", "dnf"))
        self.assertIsNone(installer.get_os_specific_pkg_name("responder", "dnf"))

    def test_falls_back_to_apt_name(self):
        """Managers without an explicit entry fall back to the Debian name."""
        self.assertEqual(installer.get_os_specific_pkg_name("nmap", "pacman"), "nmap")
        self.assertEqual(installer.get_os_specific_pkg_name("nmap"), "nmap")

    def test_macos_uses_brew_names(self):
        with mock.patch("core.installer.get_os", return_value="darwin"):
            self.assertEqual(installer.get_os_specific_pkg_name("john"), "john-jumbo")
            self.assertIsNone(installer.get_os_specific_pkg_name("enum4linux"))


class TestToolDetection(unittest.TestCase):
    """Executable detection uses the command override when present."""

    def test_netcat_checked_via_nc(self):
        def fake_which(name):
            return "/usr/bin/nc" if name == "nc" else None

        with mock.patch("shutil.which", side_effect=fake_which):
            self.assertTrue(installer.is_tool_installed("netcat"))

    def test_missing_tool_returns_false(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertFalse(installer.is_tool_installed("nmap"))


class TestLockAndRecoveryHelpers(unittest.TestCase):
    """apt lock detection and dpkg recovery helpers."""

    def test_is_lock_error_detects_markers(self):
        self.assertTrue(installer._is_lock_error("E: Could not get lock /var/lib/dpkg/lock"))
        self.assertTrue(installer._is_lock_error("Waiting for cache lock: Could not get lock"))
        self.assertFalse(installer._is_lock_error("Package installed successfully"))

    def test_needs_dpkg_recovery_detects_markers(self):
        interrupted = "dpkg was interrupted, you must manually run dpkg --configure -a"
        self.assertTrue(installer._needs_dpkg_recovery(interrupted))
        self.assertFalse(installer._needs_dpkg_recovery("E: Unable to locate package foo"))

    def test_wait_for_apt_lock_returns_true_when_free(self):
        with mock.patch("core.installer._apt_lock_holders", return_value=[]):
            self.assertTrue(installer.wait_for_apt_lock(timeout=1))

    def test_wait_for_apt_lock_times_out_when_held(self):
        with mock.patch("core.installer._apt_lock_holders", return_value=["dpkg"]):
            self.assertFalse(installer.wait_for_apt_lock(timeout=0))

    def test_apt_recover_runs_steps(self):
        calls = []

        def fake_run(cmd, env=None, timeout=300):
            calls.append(cmd)
            return 0, "ok"

        with mock.patch("core.installer._run_install_command", side_effect=fake_run):
            self.assertTrue(installer.apt_recover(pm="apt-get"))
        self.assertEqual(len(calls), 2)
        self.assertIn("dpkg", calls[0])
        self.assertIn("-f", calls[1])


class TestInstallSystemTool(unittest.TestCase):
    """install_system_tool behavior for unavailable packages and retries."""

    def test_unavailable_package_returns_message(self):
        result = installer.install_system_tool("nmap", None, "apt")
        self.assertFalse(result[0])
        self.assertIn("No apt package available", result[1])

    def test_retries_after_dpkg_interruption(self):
        outputs = iter([
            (100, "dpkg was interrupted, you must manually run 'sudo dpkg --configure -a'"),
            (0, "Setting up nmap"),
        ])

        with mock.patch("core.installer.get_os", return_value="linux"), \
                mock.patch("core.installer.wait_for_apt_lock", return_value=True), \
                mock.patch("core.installer.apt_recover", return_value=True), \
                mock.patch("core.installer._run_install_command") as run_cmd:
            run_cmd.side_effect = _next_output(outputs)
            success, output = installer.install_system_tool("nmap", "nmap", "apt")
        self.assertTrue(success)
        self.assertIn("Setting up nmap", output)

    def test_retry_after_lock_conflict(self):
        outputs = iter([
            (100, "E: Could not get lock /var/lib/dpkg/lock-frontend"),
            (0, "Setting up hydra"),
        ])

        with mock.patch("core.installer.get_os", return_value="linux"), \
                mock.patch("core.installer.wait_for_apt_lock", return_value=True), \
                mock.patch("core.installer._run_install_command") as run_cmd:
            run_cmd.side_effect = _next_output(outputs)
            success, output = installer.install_system_tool("hydra", "hydra", "apt")
        self.assertTrue(success)
        self.assertIn("Setting up hydra", output)


if __name__ == "__main__":
    unittest.main()
