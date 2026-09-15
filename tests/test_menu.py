"""
Test: core/menu.py
Covers: MainMenu (init, _set_target, _section_header, run, _toggle_learning_mode,
        _menu_profile, _menu_reports, sub-menu dispatch)
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import core.menu  # noqa: E402,F401  (imported so the fixtures below can patch its attributes)


PATCH_TARGETS = [
    "core.menu.SessionLogger",
    "core.menu.TargetProfile",
    "core.menu.supported_modules",
    "core.menu.show_dashboard",
    "core.menu.show_tools_status",
    "core.menu.set_learning_mode",
    "core.menu.get_learning_mode",
    "core.menu.os_label",
    "core.menu.console.print",
    "core.menu.questionary.select",
    "core.menu.questionary.confirm",
    "core.menu.Prompt.ask",
    "modules.crack.run",
    "modules.traffic.run",
    "modules.wireless.run",
    "modules.web.run",
    "modules.vuln.run",
    "modules.defense.run",
    "modules.recon.run",
    "modules.diff.run",
    "core.menu.cve_mod.run",
]


@pytest.fixture
def menu_mocks():
    """Mock logger, profile, questionary, and module runs for menu tests."""
    patchers = {t: patch(t) for t in PATCH_TARGETS}
    mocks = {}
    for target, p in patchers.items():
        mocks[target] = p.start()

    mocks["core.menu.supported_modules"].return_value = {
        "wireless": True, "defense": True
    }
    mocks["core.menu.SessionLogger"].return_value = MagicMock()
    mocks["core.menu.TargetProfile"].return_value = MagicMock()
    mocks["core.menu.get_learning_mode"].return_value = False
    mocks["core.menu.Prompt.ask"].return_value = "192.168.1.1"
    mocks["core.menu.os_label"].return_value = "Linux"

    yield mocks

    for p in patchers.values():
        p.stop()


class TestMainMenuInit:
    """Tests for MainMenu initialization."""

    def test_menu_initializes_with_logger_and_profile(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        assert menu.target is None
        assert menu.profile is not None
        assert menu.logger is not None
        assert menu.support is not None

    def test_menu_support_checks_wireless(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        assert "wireless" in menu.support


class TestMainMenuHelpers:
    """Tests for helper methods."""

    def test_set_target_prompts_and_updates(self, menu_mocks):
        menu_mocks["core.menu.Prompt.ask"].return_value = "10.0.0.1"
        from core.menu import MainMenu
        menu = MainMenu()
        result = menu._set_target()
        assert result == "10.0.0.1"
        assert menu.target == "10.0.0.1"

    def test_unsupported_os_returns_true(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        menu.support = {"wireless": False}
        result = menu._unsupported_os_warning("wireless")
        assert result is True

    def test_unsupported_os_returns_false_when_supported(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        menu.support = {"wireless": True}
        result = menu._unsupported_os_warning("wireless")
        assert result is False


class TestMainMenuRun:
    """Tests for the main menu loop."""

    def test_run_exits_on_exit_choice(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].return_value.ask.return_value = "exit"
        m["core.menu.questionary.confirm"].return_value.ask.return_value = True
        from core.menu import MainMenu
        menu = MainMenu()
        try:
            menu.run()
        except StopIteration:
            pass
        assert menu.logger.close.called

    def test_run_dispatches_to_tools(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].side_effect = [
            MagicMock(ask=MagicMock(return_value="tools")),
            MagicMock(ask=MagicMock(return_value="exit")),
        ]
        m["core.menu.questionary.confirm"].return_value.ask.return_value = True
        from core.menu import MainMenu
        menu = MainMenu()
        try:
            menu.run()
        except StopIteration:
            pass

    def test_run_dispatches_to_diff(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].side_effect = [
            MagicMock(ask=MagicMock(return_value="diff")),
            MagicMock(ask=MagicMock(return_value="exit")),
        ]
        m["core.menu.questionary.confirm"].return_value.ask.return_value = True
        from core.menu import MainMenu
        menu = MainMenu()
        try:
            menu.run()
        except StopIteration:
            pass
        assert m["modules.diff.run"].called

    def test_toggle_learning_mode(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        menu._toggle_learning_mode()
        assert menu_mocks["core.menu.get_learning_mode"].called


class TestMainMenuSubMenus:
    """Tests for individual sub-menu dispatch."""

    def test_menu_reports_list(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].return_value.ask.return_value = "list"
        from core.menu import MainMenu
        menu = MainMenu()
        menu._menu_reports()
        assert menu.logger.list_reports.called

    def test_menu_reports_pdf(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].return_value.ask.return_value = "pdf"
        from core.menu import MainMenu
        menu = MainMenu()
        menu._menu_reports()
        assert menu.logger.export_pdf.called

    def test_menu_profile_no_existing(self, menu_mocks):
        from core.menu import MainMenu
        menu = MainMenu()
        menu.profile.get_target.return_value = {}
        menu._menu_profile()

    def test_menu_cve_submenu(self, menu_mocks):
        m = menu_mocks
        m["core.menu.questionary.select"].return_value.ask.return_value = "from_nmap"
        from core.menu import MainMenu
        menu = MainMenu()
        menu._menu_cve()
        assert m["core.menu.cve_mod.run"].called
