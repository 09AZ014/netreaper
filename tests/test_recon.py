"""
Test: modules/recon.py
Covers: recon.run (ping_sweep, arp_scan, netdiscover, masscan, fast_ports, full_ports,
        os_detect, stealth, scripts, udp, custom) and profile integration
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def recon_mocks():
    """Mock run_command and Prompt.ask for recon tests."""
    with patch("modules.recon.run_command") as mock_run, \
         patch("modules.recon.Prompt.ask") as mock_prompt:
        mock_run.return_value = (
            "Nmap scan report for 192.168.1.1\n"
            "22/tcp open  ssh    OpenSSH 8.9\n"
            "80/tcp open  http   Apache httpd 2.4.41\n"
            "OS details: Linux 5.4\n"
        )
        mock_prompt.return_value = "nmap -p 80-443 192.168.1.1"
        yield mock_run


class TestReconRun:
    """Tests for recon.run function."""

    def test_ping_sweep_generates_nmap(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("ping_sweep", "192.168.1.0/24", mock_logger)
        assert recon_mocks.called
        cmd = recon_mocks.call_args[0][0]
        assert "nmap" in cmd
        assert "-sn" in cmd

    def test_arp_scan_is_local(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("arp_scan", "", mock_logger)
        cmd = recon_mocks.call_args[0][0]
        assert "arp-scan" in cmd

    def test_stealth_uses_anti_detection(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("stealth", "192.168.1.1", mock_logger)
        cmd = recon_mocks.call_args[0][0]
        assert "-T2" in cmd or "-D" in cmd

    def test_full_ports_is_comprehensive(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("full_ports", "10.0.0.1", mock_logger)
        cmd = recon_mocks.call_args[0][0]
        assert "-p-" in cmd

    def test_udp_scan_is_udp(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("udp", "10.0.0.1", mock_logger)
        cmd = recon_mocks.call_args[0][0]
        assert "-sU" in cmd

    def test_updates_profile_when_available(self, recon_mocks):
        mock_logger = MagicMock()
        mock_profile = MagicMock()
        mock_profile.get_target.return_value = {"os": ""}
        from modules.recon import run
        run("os_detect", "192.168.1.1", mock_logger, profile=mock_profile)
        assert mock_profile.update_target.called

    def test_custom_prompts_for_command(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("custom", "192.168.1.1", mock_logger)
        assert recon_mocks.called

    def test_unknown_scan_does_not_crash(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        try:
            run("nonexistent", "target", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report(self, recon_mocks):
        mock_logger = MagicMock()
        from modules.recon import run
        run("fast_ports", "192.168.1.1", mock_logger)
        assert mock_logger.save_report.called
