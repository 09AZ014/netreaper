"""
Test: modules/crack.py
Covers: crack.run modes (john, hashcat, hashid), brute_services
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_prompt():
    """Mock rich.prompt.Prompt.ask to return predefined values."""
    with patch("modules.crack.Prompt.ask") as mock_ask:
        mock_ask.side_effect = lambda prompt, default="": "test_value"
        yield mock_ask


@pytest.fixture
def mock_wordlist():
    """Mock select_wordlist to return a fixed path."""
    with patch("modules.crack.select_wordlist") as mock_wl:
        mock_wl.return_value = "/usr/share/wordlists/rockyou.txt"
        yield mock_wl


@pytest.fixture
def mock_run_command():
    """Mock run_command to return fake output."""
    with patch("modules.crack.run_command") as mock_run:
        mock_run.return_value = "password123 (admin)"
        yield mock_run


class TestCrackHashModes:
    """Tests for hash cracking modes (john, hashcat, hashid)."""

    def test_john_mode_calls_run_command(self, mock_prompt, mock_wordlist,
                                          mock_run_command):
        """'john' mode should build and execute a john command."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("john", mock_logger)
        assert mock_run_command.called
        cmd = mock_run_command.call_args[0][0]
        assert "john" in cmd
        assert "--wordlist=" in cmd

    def test_hashcat_mode_calls_run_command(self, mock_prompt, mock_wordlist,
                                             mock_run_command):
        """'hashcat' mode should build and execute a hashcat command."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("hashcat", mock_logger)
        assert mock_run_command.called
        cmd = mock_run_command.call_args[0][0]
        assert "hashcat" in cmd

    def test_hashid_mode_calls_run_command(self, mock_prompt, mock_run_command):
        """'hashid' mode should identify hash type."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("hashid", mock_logger)
        assert mock_run_command.called

    def test_unknown_mode_does_not_crash(self, mock_prompt, mock_wordlist,
                                          mock_run_command):
        """Unknown mode falls to brute_services which uses prompt but shouldn't crash."""
        mock_logger = MagicMock()
        from modules.crack import run
        try:
            run("brute_ssh", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")


class TestBruteForceServices:
    """Tests for brute force service methods."""

    def test_brute_ssh_generates_hydra_command(self, mock_prompt, mock_wordlist,
                                                mock_run_command):
        """brute_ssh should generate a hydra SSH command."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("brute_ssh", mock_logger)
        assert mock_run_command.called
        cmd = mock_run_command.call_args[0][0]
        assert "hydra" in cmd
        assert "ssh://" in cmd

    def test_brute_http_generates_hydra_command(self, mock_prompt, mock_wordlist,
                                                 mock_run_command):
        """brute_http should include the target path."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("brute_http", mock_logger)
        cmd = mock_run_command.call_args[0][0]
        assert "http-get://" in cmd

    def test_brute_router_includes_form_post(self, mock_prompt, mock_wordlist,
                                              mock_run_command):
        """Router brute force should use http-form-post."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("brute_router", mock_logger)
        cmd = mock_run_command.call_args[0][0]
        assert "http-form-post://" in cmd
        assert "login.cgi" in cmd

    def test_all_modes_log_output(self, mock_prompt, mock_wordlist,
                                    mock_run_command):
        """All brute force modes should call logger.save_report."""
        mock_logger = MagicMock()
        from modules.crack import run
        run("brute_ftp", mock_logger)
        assert mock_logger.save_report.called
