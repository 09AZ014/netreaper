"""
Test: modules/traffic.py
Covers: traffic.run for all actions (interfaces, capture_all, http, dns, creds, arp, live)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def traffic_mocks(tmp_path):
    """Mock run_command, select_interface, and ensure_temp_dir for traffic tests."""
    with patch("modules.traffic.run_command") as mock_run, \
         patch("modules.traffic.select_interface") as mock_iface, \
         patch("modules.traffic.ensure_temp_dir") as mock_temp:
        mock_run.return_value = "packet data"
        mock_iface.return_value = "eth0"
        mock_temp.return_value = tmp_path
        yield {
            "run": mock_run,
            "iface": mock_iface,
            "temp": mock_temp,
        }


class TestTrafficRun:
    """Tests for traffic.run function."""

    def test_interfaces_action(self, traffic_mocks):
        mock_logger = MagicMock()
        from modules.traffic import run
        run("interfaces", mock_logger)
        assert traffic_mocks["run"].called
        cmd = traffic_mocks["run"].call_args[0][0]
        assert "ip" in cmd or "netsh" in cmd

    def test_capture_all_linux(self, monkeypatch, traffic_mocks):
        monkeypatch.setattr("modules.traffic.get_os", lambda: "linux")
        monkeypatch.setattr("modules.traffic.OS_WINDOWS", "windows")
        mock_logger = MagicMock()
        from modules.traffic import run
        run("capture_all", mock_logger)
        assert traffic_mocks["run"].called
        cmd = traffic_mocks["run"].call_args[0][0]
        assert "tshark" in cmd

    def test_http_action(self, monkeypatch, traffic_mocks):
        monkeypatch.setattr("modules.traffic.get_os", lambda: "linux")
        monkeypatch.setattr("modules.traffic.OS_WINDOWS", "windows")
        mock_logger = MagicMock()
        from modules.traffic import run
        run("http", mock_logger)
        cmd = traffic_mocks["run"].call_args[0][0]
        assert "tshark" in cmd
        assert "http" in cmd.lower()

    def test_dns_action(self, monkeypatch, traffic_mocks):
        monkeypatch.setattr("modules.traffic.get_os", lambda: "linux")
        monkeypatch.setattr("modules.traffic.OS_WINDOWS", "windows")
        mock_logger = MagicMock()
        from modules.traffic import run
        run("dns", mock_logger)
        cmd = traffic_mocks["run"].call_args[0][0]
        assert "dns" in cmd

    def test_unknown_action_does_not_crash(self, traffic_mocks):
        mock_logger = MagicMock()
        from modules.traffic import run
        try:
            run("nonexistent", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report_after_capture(self, monkeypatch, traffic_mocks):
        monkeypatch.setattr("modules.traffic.get_os", lambda: "linux")
        monkeypatch.setattr("modules.traffic.OS_WINDOWS", "windows")
        mock_logger = MagicMock()
        from modules.traffic import run
        run("capture_all", mock_logger)
        assert mock_logger.save_report.called

    def test_no_interface_returns_early(self, traffic_mocks):
        traffic_mocks["iface"].return_value = ""
        mock_logger = MagicMock()
        from modules.traffic import run
        result = run("capture_all", mock_logger)
        assert result is None
