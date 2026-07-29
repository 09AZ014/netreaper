"""
Test: modules/web.py
Covers: web.run (gobuster, ffuf, sqlmap, nikto, headers, ssl)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def web_mocks(tmp_path):
    """Mock run_command, select_wordlist, ensure_temp_dir, and Prompt.ask for web tests."""
    with patch("modules.web.run_command") as mock_run, \
         patch("modules.web.select_wordlist") as mock_wl, \
         patch("modules.web.ensure_temp_dir") as mock_temp, \
         patch("modules.web.Prompt.ask") as mock_prompt:
        mock_run.return_value = "web scan output"
        mock_wl.return_value = "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"
        mock_temp.return_value = tmp_path
        mock_prompt.return_value = "id=1"
        yield {
            "run": mock_run,
            "wl": mock_wl,
            "temp": mock_temp,
            "prompt": mock_prompt,
        }


class TestWebRun:
    """Tests for web.run function."""

    def test_gobuster_generates_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("gobuster", "example.com", mock_logger)
        assert web_mocks["run"].called
        cmd = web_mocks["run"].call_args[0][0]
        assert "gobuster" in cmd

    def test_ffuf_generates_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("ffuf", "example.com", mock_logger)
        cmd = web_mocks["run"].call_args[0][0]
        assert "ffuf" in cmd
        assert "FUZZ" in cmd

    def test_sqlmap_generates_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("sqlmap", "example.com", mock_logger)
        cmd = web_mocks["run"].call_args[0][0]
        assert "sqlmap" in cmd

    def test_nikto_generates_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("nikto", "example.com", mock_logger)
        cmd = web_mocks["run"].call_args[0][0]
        assert "nikto" in cmd

    def test_headers_generates_curl_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("headers", "example.com", mock_logger)
        cmd = web_mocks["run"].call_args[0][0]
        assert "curl" in cmd

    def test_ssl_generates_sslscan_command(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("ssl", "example.com", mock_logger)
        cmd = web_mocks["run"].call_args[0][0]
        assert "sslscan" in cmd

    def test_unknown_action_does_not_crash(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        try:
            run("nonexistent", "target", mock_logger)
            assert True
        except Exception as e:
            pytest.fail(f"run raised: {e}")

    def test_saves_report(self, web_mocks):
        mock_logger = MagicMock()
        from modules.web import run
        run("headers", "example.com", mock_logger)
        assert mock_logger.save_report.called
