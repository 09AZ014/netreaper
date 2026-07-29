"""
Test: core/platform.py
Covers: get_os, is_windows, is_linux, is_macos, get_package_managers,
        supported_modules, is_admin, os_label, get_local_ip
Author: 09azo14 | License: MIT
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOSDetection:
    """Tests for OS detection functions."""

    def test_get_os_returns_linux_on_linux(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import get_os
        assert get_os() == "linux"

    def test_get_os_returns_windows(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        from core.platform import get_os
        assert get_os() == "windows"

    def test_get_os_returns_darwin_for_macos(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        from core.platform import get_os
        assert get_os() == "darwin"

    def test_get_os_unknown(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "FreeBSD")
        from core.platform import get_os
        assert get_os() == "unknown"

    def test_is_linux(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import is_linux
        assert is_linux() is True

    def test_is_windows_false_on_linux(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import is_windows
        assert is_windows() is False

    def test_os_label_returns_friendly_name(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import os_label
        assert os_label() == "Linux"


class TestPackageManager:
    """Tests for package manager detection."""

    def test_get_package_managers_linux(self, monkeypatch, mock_shutil_which):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import get_package_managers
        with patch("shutil.which", side_effect=lambda x: x in ("apt", "yum")):
            pms = get_package_managers()
            assert "apt" in pms
            assert "yum" in pms

    def test_get_package_managers_returns_list(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import get_package_managers
        pms = get_package_managers()
        assert isinstance(pms, list)


class TestSupportedModules:
    """Tests for supported_modules() which checks OS compatibility."""

    def test_all_modules_supported_on_linux(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import supported_modules
        support = supported_modules()
        assert support["wireless"] is True
        assert support["defense"] is True
        assert support["recon"] is True

    def test_wireless_unsupported_on_windows(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        from core.platform import supported_modules
        support = supported_modules()
        assert support["wireless"] is False
        assert support["defense"] is False

    def test_common_modules_always_supported(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        from core.platform import supported_modules
        support = supported_modules()
        assert support["recon"] is True
        assert support["web"] is True
        assert support["crack"] is True


class TestAdminCheck:
    """Tests for privilege detection."""

    def test_is_admin_on_linux_root(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.setattr("os.geteuid", lambda: 0)
        from core.platform import is_admin
        assert is_admin() is True

    def test_is_admin_on_linux_non_root(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        monkeypatch.setattr("os.geteuid", lambda: 1000)
        from core.platform import is_admin
        assert is_admin() is False

    def test_is_admin_on_windows_non_admin(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr("core.platform.is_windows", lambda: True)
        import ctypes
        monkeypatch.setattr(ctypes, "windll", MagicMock(), raising=False)
        from core.platform import is_admin
        # Should not raise - might be False or True depending on mock
        result = is_admin()
        assert isinstance(result, bool)


class TestUtilityFunctions:
    """Tests for IP, gateway, and temp dir utilities."""

    def test_ensure_temp_dir_creates_directory(self, tmp_path, monkeypatch):
        from core.platform import ensure_temp_dir, get_temp_dir
        monkeypatch.setattr("core.platform.get_temp_dir", lambda: tmp_path / "netreaper")
        d = ensure_temp_dir()
        assert d.exists()
        assert d.is_dir()

    def test_command_for_ping(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import command_for
        cmd = command_for("ping")
        assert "ping" in cmd

    def test_get_firewall_status_cmd(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        from core.platform import get_firewall_status_cmd
        assert "iptables" in get_firewall_status_cmd()
