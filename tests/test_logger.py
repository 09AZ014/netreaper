"""
Test: core/logger.py
Covers: SessionLogger (init, log_command, save_report, list_reports, close, export_pdf)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSessionLoggerInit:
    """Tests for SessionLogger initialization."""

    def test_logger_creates_session_dir(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            assert logger.session_dir.exists()
            assert logger.session_dir.is_dir()
            logger.close()

    def test_logger_creates_log_file(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            assert logger.log_file.exists()
            assert logger.log_file.is_file()
            logger.close()

    def test_session_id_is_timestamp_format(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            assert len(logger.session_id) == 19
            assert "-" in logger.session_id
            assert "_" in logger.session_id
            logger.close()


class TestSessionLoggerCommands:
    """Tests for command logging and history."""

    def test_log_command_appends_to_history(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            logger.log_command("test", "echo hello", "output", "127.0.0.1")
            assert len(logger.command_history) == 1
            assert logger.command_history[0] == "echo hello"
            logger.close()

    def test_log_command_writes_to_file(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            logger.log_command("test", "echo hello", "output", "127.0.0.1")
            content = logger.log_file.read_text()
            assert "echo hello" in content
            assert "output" in content
            assert "test" in content
            logger.close()

    def test_command_history_capped_at_50(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            for i in range(60):
                logger.log_command("test", f"cmd_{i}", f"out_{i}", "target")
            assert len(logger.command_history) == 50
            # Last command should be present
            assert logger.command_history[-1] == "cmd_59"
            logger.close()


class TestSessionLoggerReports:
    """Tests for report saving."""

    def test_save_report_creates_file(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            path = logger.save_report("test_report", "test content")
            assert Path(path).exists()
            assert Path(path).read_text() == "test content"
            logger.close()

    def test_save_report_with_different_format(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            path = logger.save_report("test", "html content", fmt="html")
            assert str(path).endswith(".html")
            logger.close()

    def test_save_html_report_creates_html(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            path = logger.save_html_report("test", "Test Title", "<p>Body</p>")
            assert path.exists()
            html = path.read_text()
            assert "<!DOCTYPE html>" in html
            assert "Test Title" in html
            assert "<p>Body</p>" in html
            logger.close()


class TestSessionLoggerMisc:
    """Tests for list_reports, close, export_pdf."""

    def test_list_reports_no_reports_yet(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            try:
                logger.list_reports()
                assert True
            except Exception as e:
                pytest.fail(f"list_reports raised: {e}")
            logger.close()

    def test_close_writes_session_ended(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            logger.close()
            content = logger.log_file.read_text()
            assert "Session ended" in content

    def test_export_pdf_without_fpdf(self, tmp_path):
        with patch("core.logger.REPORTS_DIR", tmp_path):
            from core.logger import SessionLogger
            logger = SessionLogger()
            with patch.dict(sys.modules, {"fpdf": None}):
                result = logger.export_pdf()
                assert result is None
            logger.close()
