"""
Test: modules/vuln.py
Covers: vuln.run (nmap_vuln, nmap_exploit, ssl_vuln, smb_enum, lynis, searchsploit)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def vuln_mocks():
    """Mock run_command and Prompt.ask for vuln tests."""
    with patch("modules.vuln.run_command") as mock_run, \
         patch("modules.vuln.Prompt.ask") as mock_prompt:
        mock_run.return_value = "vuln scan output"
        mock_prompt.return_value = "apache 2.4"
        yield mock_run


class TestVulnRun:
    """Tests for vuln.run function."""

    def test_nmap_vuln_generates_nmap_command(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        run("nmap_vuln", "192.168.1.1", mock_logger)
        assert vuln_mocks.called
        cmd = vuln_mocks.call_args[0][0]
        assert "nmap" in cmd
        assert "vuln" in cmd

    def test_nmap_exploit_generates_nmap_command(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        run("nmap_exploit", "192.168.1.1", mock_logger)
        cmd = vuln_mocks.call_args[0][0]
        assert "nmap" in cmd
        assert "exploit" in cmd

    def test_lynis_is_local(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        run("lynis", "local", mock_logger)
        cmd = vuln_mocks.call_args[0][0]
        assert "lynis" in cmd
        assert "audit" in cmd

    def test_searchsploit_uses_prompt(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        run("searchsploit", "192.168.1.1", mock_logger)
        assert vuln_mocks.called

    def test_unknown_scan_does_not_crash(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        try:
            run("nonexistent", "192.168.1.1", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report(self, vuln_mocks):
        mock_logger = MagicMock()
        from modules.vuln import run
        run("nmap_vuln", "192.168.1.1", mock_logger)
        assert mock_logger.save_report.called
