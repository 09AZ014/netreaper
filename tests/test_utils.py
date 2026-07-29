"""
NetReaper - Tests for core/utils.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.utils import sanitize_for_shell, build_command, set_learning_mode, get_learning_mode


class TestUtils(unittest.TestCase):
    def test_sanitize_for_shell_quotes_special_chars(self):
        self.assertEqual(sanitize_for_shell("; rm -rf /"), "'; rm -rf /'")
        self.assertEqual(sanitize_for_shell("192.168.1.1"), "192.168.1.1")

    def test_build_command_quotes_inputs(self):
        cmd = build_command("nmap -sV {target}", target="192.168.1.1")
        self.assertIn("192.168.1.1", cmd)
        self.assertIn("nmap", cmd)

    def test_learning_mode_toggle(self):
        set_learning_mode(False)
        self.assertFalse(get_learning_mode())
        set_learning_mode(True)
        self.assertTrue(get_learning_mode())
        set_learning_mode(False)


if __name__ == "__main__":
    unittest.main()
