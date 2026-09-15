"""
NetReaper - Tests for core/explanations.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.explanations import explain_command  # noqa: E402


class TestExplanations(unittest.TestCase):
    def test_keyword_matching(self):
        mock_console = MagicMock()
        explain_command("nmap -sV 192.168.1.1", mock_console)
        mock_console.print.assert_called()
        output = mock_console.print.call_args[0][0]
        self.assertIn("Learning", output)

    def test_unknown_command(self):
        mock_console = MagicMock()
        explain_command("some_unknown_tool", mock_console)
        mock_console.print.assert_called()
        output = mock_console.print.call_args[0][0]
        self.assertIn("Learning", output)


if __name__ == "__main__":
    unittest.main()
