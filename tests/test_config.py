"""
NetReaper - Tests for core/config.py
Author: 09azo14 | License: MIT
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import config as config_module  # noqa: E402

# Empty values are ignored by Config._apply_env, so this neutralizes any
# NETREAPER_* variables that may be set in the test environment.
_NO_ENV = {name: "" for name in config_module.ENV_MAP.values()}


class TestConfigDefaults(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_defaults_present_without_file(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("target"), "")
        self.assertEqual(cfg.get("interface"), "")
        self.assertEqual(cfg.get("wordlist"), "")
        self.assertEqual(cfg.get("wordlist_dir"), "")
        self.assertEqual(cfg.get("nvd_api_key"), "")
        self.assertFalse(cfg.get("learning_mode"))
        self.assertEqual(cfg.get_timeout("command"), 300)
        self.assertEqual(cfg.get_timeout("scan"), 900)
        self.assertEqual(cfg.get_timeout("install"), 420)

    def test_watch_defaults(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("watch_interval"), 300)
        self.assertEqual(cfg.get("watch_webhook"), "")

    def test_unknown_key_returns_default(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertIsNone(cfg.get("does_not_exist"))
        self.assertEqual(cfg.get("does_not_exist", "fallback"), "fallback")

    def test_malformed_file_falls_back_to_defaults(self):
        self.path.write_text("{not valid json", encoding="utf-8")
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("target"), "")


class TestConfigPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "nested" / "config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_creates_file_and_parent_dirs(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
            saved = cfg.save()
        self.assertTrue(saved.exists())
        self.assertEqual(saved, self.path)

    def test_set_and_reload_roundtrip(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
            cfg.set("target", "192.168.1.0/24")
            cfg.set("interface", "eth0")
            reloaded = config_module.Config(path=self.path)
        self.assertEqual(reloaded.get("target"), "192.168.1.0/24")
        self.assertEqual(reloaded.get("interface"), "eth0")

    def test_update_writes_multiple_values(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
            cfg.update(target="10.0.0.1", wordlist_dir="/opt/lists")
            data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["target"], "10.0.0.1")
        self.assertEqual(data["wordlist_dir"], "/opt/lists")

    def test_nested_timeouts_merge_keeps_other_defaults(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"timeouts": {"command": 45}}), encoding="utf-8")
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get_timeout("command"), 45)
        self.assertEqual(cfg.get_timeout("scan"), 900)

    def test_get_timeout_handles_bad_value(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"timeouts": {"command": "soon"}}), encoding="utf-8")
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get_timeout("command"), 300)


class TestConfigEnvOverrides(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_env_overrides_file_values(self):
        env = {"NETREAPER_TARGET": "172.16.0.1", "NETREAPER_NVD_API_KEY": "secret-key"}
        with mock.patch.dict(os.environ, env):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("target"), "172.16.0.1")
        self.assertEqual(cfg.get("nvd_api_key"), "secret-key")

    def test_watch_env_overrides(self):
        env = {
            "NETREAPER_WATCH_INTERVAL": "60",
            "NETREAPER_WATCH_WEBHOOK": "http://hook.test/alerts",
        }
        with mock.patch.dict(os.environ, env):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("watch_interval"), "60")
        self.assertEqual(cfg.get("watch_webhook"), "http://hook.test/alerts")

    def test_wordlist_env_override(self):
        with mock.patch.dict(os.environ, {"NETREAPER_WORDLIST": "/opt/list.txt"}):
            cfg = config_module.Config(path=self.path)
        self.assertEqual(cfg.get("wordlist"), "/opt/list.txt")

    def test_learning_mode_env_parsed_as_bool(self):
        with mock.patch.dict(os.environ, {"NETREAPER_LEARNING_MODE": "true"}):
            self.assertTrue(config_module.Config(path=self.path).get("learning_mode"))
        with mock.patch.dict(os.environ, {"NETREAPER_LEARNING_MODE": "no"}):
            self.assertFalse(config_module.Config(path=self.path).get("learning_mode"))


class TestConfigDisplay(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "config.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_as_text_masks_api_key(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
            cfg.set("nvd_api_key", "super-secret")
            text = cfg.as_text()
        self.assertIn("*** set ***", text)
        self.assertNotIn("super-secret", text)

    def test_as_text_lists_all_keys(self):
        with mock.patch.dict(os.environ, _NO_ENV):
            cfg = config_module.Config(path=self.path)
        text = cfg.as_text()
        for key in config_module.DEFAULTS:
            self.assertIn(key, text)


class TestConfigSingleton(unittest.TestCase):
    def test_get_config_returns_same_instance(self):
        first = config_module.get_config()
        second = config_module.get_config()
        self.assertIs(first, second)

    def test_reset_config_rebuilds_instance(self):
        first = config_module.get_config()
        second = config_module.reset_config()
        self.assertIsNot(first, second)


if __name__ == "__main__":
    unittest.main()
