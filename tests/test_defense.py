"""
Test: modules/defense.py
Covers: defense.run (fw_status, block_ip, connections, arp_table, failed_login, processes,
        fail2ban, listening, Windows variants)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def defense_mocks(monkeypatch):
    """Mock run_command, confirm_action, and Prompt.ask for defense tests."""
    with patch("modules.defense.run_command") as mock_run, \
         patch("modules.defense.confirm_action") as mock_confirm, \
         patch("modules.defense.Prompt.ask") as mock_prompt:
        mock_run.return_value = "defense output"
        mock_confirm.return_value = True
        mock_prompt.return_value = "192.168.1.100"
        monkeypatch.setattr("modules.defense.get_os", lambda: "linux")
        monkeypatch.setattr("modules.defense.OS_WINDOWS", "windows")
        yield {
            "run": mock_run,
            "confirm": mock_confirm,
            "prompt": mock_prompt,
        }


class TestDefenseLinux:
    """Tests for defense module on Linux."""

    def test_fw_status_generates_iptables(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("fw_status", mock_logger)
        assert defense_mocks["run"].called
        cmd = defense_mocks["run"].call_args[0][0]
        assert "iptables" in cmd

    def test_connections_generates_ss_command(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("connections", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "ss" in cmd or "tulnp" in cmd

    def test_failed_login_generates_grep(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("failed_login", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "Failed password" in cmd or "auth.log" in cmd

    def test_processes_generates_ps_command(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("processes", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "ps" in cmd

    def test_fail2ban_generates_fail2ban_command(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("fail2ban", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "fail2ban-client" in cmd

    def test_listening_generates_lsof_command(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("listening", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "lsof" in cmd

    def test_arp_table_command(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("arp_table", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "arp" in cmd

    def test_block_ip_with_confirmation(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("block_ip", mock_logger)
        assert defense_mocks["run"].called

    def test_block_ip_cancelled(self, defense_mocks):
        mock_logger = MagicMock()
        defense_mocks["confirm"].return_value = False
        from modules.defense import run
        run("block_ip", mock_logger)
        assert not defense_mocks["run"].called


class TestDefenseWindows:
    """Tests for defense module on Windows."""

    def test_windows_fw_status(self, defense_mocks, monkeypatch):
        monkeypatch.setattr("modules.defense.get_os", lambda: "windows")
        mock_logger = MagicMock()
        from modules.defense import run
        run("fw_status", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "netsh" in cmd

    def test_windows_connections(self, defense_mocks, monkeypatch):
        monkeypatch.setattr("modules.defense.get_os", lambda: "windows")
        mock_logger = MagicMock()
        from modules.defense import run
        run("connections", mock_logger)
        cmd = defense_mocks["run"].call_args[0][0]
        assert "netstat" in cmd


class TestDefenseEdgeCases:
    """Edge case tests for defense module."""

    def test_unknown_action_does_not_crash(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        try:
            run("nonexistent", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report(self, defense_mocks):
        mock_logger = MagicMock()
        from modules.defense import run
        run("fw_status", mock_logger)
        assert mock_logger.save_report.called
