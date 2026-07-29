"""
Test: modules/wireless.py
Covers: wireless.run (monitor_on, monitor_off, scan, capture_hs, deauth, crack_wpa, wifite)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def wireless_mocks(monkeypatch):
    """Mock run_command, select_interface, supported_modules, and Prompt.ask for wireless tests."""
    with patch("modules.wireless.run_command") as mock_run, \
         patch("modules.wireless.select_interface") as mock_iface, \
         patch("modules.wireless.supported_modules") as mock_support, \
         patch("modules.wireless.Prompt.ask") as mock_prompt:
        mock_run.return_value = "wifi output"
        mock_iface.return_value = "wlan0"
        mock_support.return_value = {"wireless": True}
        mock_prompt.return_value = "test_value"
        yield {
            "run": mock_run,
            "iface": mock_iface,
            "support": mock_support,
            "prompt": mock_prompt,
        }


class TestWirelessRun:
    """Tests for wireless.run function."""

    def test_unsupported_on_windows(self, wireless_mocks, monkeypatch):
        wireless_mocks["support"].return_value = {"wireless": False}
        monkeypatch.setattr("modules.wireless.os_label", lambda: "Windows")
        mock_logger = MagicMock()
        from modules.wireless import run
        result = run("scan", mock_logger)
        assert result is None

    def test_monitor_on_generates_airmon_command(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        run("monitor_on", mock_logger)
        assert wireless_mocks["run"].called
        cmd = wireless_mocks["run"].call_args[0][0]
        assert "airmon-ng" in cmd

    def test_scan_generates_airodump_command(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        run("scan", mock_logger)
        cmd = wireless_mocks["run"].call_args[0][0]
        assert "airodump-ng" in cmd

    def test_deauth_generates_aireplay_command(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        run("deauth", mock_logger)
        cmd = wireless_mocks["run"].call_args[0][0]
        assert "aireplay-ng" in cmd
        assert "--deauth" in cmd

    def test_crack_wpa_generates_aircrack_command(self, wireless_mocks):
        mock_logger = MagicMock()
        wireless_mocks["prompt"].side_effect = [
            "/tmp/capture.cap",
            "/usr/share/wordlists/rockyou.txt",
        ]
        from modules.wireless import run
        run("crack_wpa", mock_logger)
        cmd = wireless_mocks["run"].call_args[0][0]
        assert "aircrack-ng" in cmd

    def test_wifite_generates_wifite_command(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        run("wifite", mock_logger)
        cmd = wireless_mocks["run"].call_args[0][0]
        assert "wifite" in cmd

    def test_unknown_action_does_not_crash(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        try:
            run("nonexistent", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report(self, wireless_mocks):
        mock_logger = MagicMock()
        from modules.wireless import run
        run("scan", mock_logger)
        assert mock_logger.save_report.called
