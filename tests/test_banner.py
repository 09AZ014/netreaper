"""
Test: core/banner.py
Covers: show_banner function, banner constant
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBannerModule:
    """Tests for the banner display module."""

    def test_banner_constant_exists(self):
        """BANNER string should be defined and non-empty."""
        from core.banner import BANNER
        assert BANNER is not None
        assert len(BANNER) > 50
        assert "NetReaper" in BANNER or "██" in BANNER

    def test_show_banner_calls_console(self):
        """show_banner() should call console.clear() and console.print()."""
        with patch("core.banner.console.clear") as mock_clear, \
             patch("core.banner.console.print") as mock_print, \
             patch("time.sleep") as mock_sleep:
            from core.banner import show_banner
            show_banner()
            assert mock_clear.called
            assert mock_print.called
            assert mock_sleep.called

    def test_show_banner_renders_without_exception(self):
        """show_banner() should not raise any exception."""
        with patch("core.banner.console.clear"), \
             patch("core.banner.console.print"), \
             patch("time.sleep"):
            from core.banner import show_banner
            try:
                show_banner()
                assert True
            except Exception as e:
                pytest.fail(f"show_banner raised: {e}")
