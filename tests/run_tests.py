#!/usr/bin/env python3
"""
NetReaper - Test runner
Author: 09azo14 | License: MIT
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

discovered = unittest.defaultTestLoader.discover(
    str(Path(__file__).parent), pattern="test_*.py"
)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(discovered)
sys.exit(0 if result.wasSuccessful() else 1)
