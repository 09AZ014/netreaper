"""
NetReaper - Tests for core/utils.py
Author: 09azo14 | License: MIT
"""

import os
import tempfile
import unittest
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import (  # noqa: E402
    sanitize_for_shell, build_command, set_learning_mode, get_learning_mode,
)


class TestUtils(unittest.TestCase):
    def test_sanitize_for_shell_quotes_special_chars(self):
        self.assertEqual(sanitize_for_shell("; rm -rf /"), "'; rm -rf /'")
        self.assertEqual(sanitize_for_shell("192.168.1.1"), "192.168.1.1")

    def test_build_command_quotes_inputs(self):
        cmd = build_command("nmap -sV {target}", target="192.168.1.1")
        self.assertIn("192.168.1.1", cmd)
        self.assertIn("nmap", cmd)

    def test_select_wordlist_uses_configured_file_without_prompting(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            from core import utils
            with mock.patch("core.utils.get_config") as get_cfg:
                get_cfg.return_value.get.return_value = path
                with mock.patch("questionary.select") as select:
                    self.assertEqual(utils.select_wordlist(), path)
            select.assert_not_called()
        finally:
            os.remove(path)

    def test_select_wordlist_falls_back_when_configured_file_missing(self):
        from core import utils
        with mock.patch("core.utils.get_config") as get_cfg:
            get_cfg.return_value.get.side_effect = lambda key, default=None: (
                "/no/such/wordlist.txt" if key == "wordlist" else ""
            )
            with mock.patch("questionary.select") as select:
                select.return_value.ask.return_value = "/built/in.txt"
                self.assertEqual(utils.select_wordlist(), "/built/in.txt")

    def test_learning_mode_toggle(self):
        set_learning_mode(False)
        self.assertFalse(get_learning_mode())
        set_learning_mode(True)
        self.assertTrue(get_learning_mode())
        set_learning_mode(False)


if __name__ == "__main__":
    unittest.main()
