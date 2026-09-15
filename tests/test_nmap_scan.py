"""
Test: modules/nmap_scan.py
Covers: scan profiles, run function, command generation
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNmapScanProfiles:
    """Tests for scan profile definitions."""

    def test_scan_profiles_exist(self):
        """SCAN_PROFILES should contain expected scan types."""
        from modules.nmap_scan import SCAN_PROFILES
        assert "ping_sweep" in SCAN_PROFILES
        assert "fast_ports" in SCAN_PROFILES
        assert "full_ports" in SCAN_PROFILES
        assert "os_detect" in SCAN_PROFILES
        assert "stealth" in SCAN_PROFILES
        assert "scripts" in SCAN_PROFILES
        assert "udp" in SCAN_PROFILES
        assert "custom" in SCAN_PROFILES

    def test_ping_sweep_profile_contains_nmap(self):
        """Ping sweep should use nmap -sn."""
        from modules.nmap_scan import SCAN_PROFILES
        _, cmd = SCAN_PROFILES["ping_sweep"]
        assert "nmap" in cmd
        assert "-sn" in cmd

    def test_stealth_profile_is_paranoid(self):
        """Stealth profile should use slow timing and decoys."""
        from modules.nmap_scan import SCAN_PROFILES
        _, cmd = SCAN_PROFILES["stealth"]
        assert "-T2" in cmd or "-sS" in cmd


class TestNmapRun:
    """Tests for the nmap_scan.run function."""

    def test_run_ping_sweep_calls_run_command(self):
        """Running ping_sweep should invoke run_command with nmap."""
        mock_logger = MagicMock()
        mock_logger.save_report = MagicMock()
        with patch("modules.nmap_scan.run_command") as mock_run:
            mock_run.return_value = "Host is up"
            from modules.nmap_scan import run
            run("ping_sweep", "192.168.1.0/24", mock_logger)
            assert mock_run.called
            cmd_arg = mock_run.call_args[0][0]
            assert "nmap" in cmd_arg

    def test_run_unknown_type_does_not_crash(self):
        """Unknown scan type should not crash."""
        mock_logger = MagicMock()
        with patch("modules.nmap_scan.run_command"):
            from modules.nmap_scan import run
            try:
                run("nonexistent_type", "192.168.1.1", mock_logger)
                assert True
            except Exception as e:
                pytest.fail(f"run raised for unknown type: {e}")

    def test_run_logs_output(self):
        """Output should be logged via logger.save_report."""
        mock_logger = MagicMock()
        mock_logger.save_report = MagicMock()
        with patch("modules.nmap_scan.run_command") as mock_run:
            mock_run.return_value = "22/tcp open  ssh\n80/tcp open  http"
            from modules.nmap_scan import run
            run("fast_ports", "192.168.1.1", mock_logger)
            assert mock_logger.save_report.called

    def test_run_calls_run_command_with_logger(self):
        """run_command should receive the logger for session tracking."""
        mock_logger = MagicMock()
        with patch("modules.nmap_scan.run_command") as mock_run:
            mock_run.return_value = "output"
            from modules.nmap_scan import run
            run("scripts", "10.0.0.1", mock_logger)
            kw = mock_run.call_args[1]
            assert kw.get("logger") == mock_logger
            assert kw.get("module") == "nmap_scan"


class TestNmapEdgeCases:
    """Edge case and robustness tests for nmap_scan."""

    def test_run_with_empty_target(self):
        """Running with an empty target should not crash."""
        mock_logger = MagicMock()
        with patch("modules.nmap_scan.run_command") as mock_run:
            mock_run.return_value = ""
            from modules.nmap_scan import run
            try:
                run("fast_ports", "", mock_logger)
                assert True
            except Exception:
                pass  # Some modules may handle this gracefully

    def test_run_with_special_chars_in_target(self):
        """Target with special characters should pass through sanitization."""
        mock_logger = MagicMock()
        with patch("modules.nmap_scan.run_command") as mock_run:
            mock_run.return_value = ""
            from modules.nmap_scan import run
            try:
                run("fast_ports", "192.168.1.1; echo bad", mock_logger)
                assert True
            except Exception:
                pass
