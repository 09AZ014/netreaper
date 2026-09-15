"""
NetReaper - Tests for core/profile.py
Author: 09azo14 | License: MIT
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import core.profile as profile_module  # noqa: E402


class TestTargetProfile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_path = profile_module.PROFILE_PATH
        profile_module.PROFILE_PATH = Path(self.tmpdir) / "target_profile.json"
        self.profile = profile_module.TargetProfile()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        profile_module.PROFILE_PATH = self.orig_path

    def test_update_target_creates_profile(self):
        self.profile.update_target("192.168.1.1", ports=["tcp/80"], os="Linux")
        info = self.profile.get_target("192.168.1.1")
        self.assertEqual(info["ip"], "192.168.1.1")
        self.assertIn("tcp/80", info["ports"])
        self.assertEqual(info["os"], "Linux")

    def test_ports_are_merged(self):
        self.profile.add_ports("192.168.1.1", ["tcp/22", "tcp/80"])
        self.profile.add_ports("192.168.1.1", ["tcp/443"])
        info = self.profile.get_target("192.168.1.1")
        self.assertIn("tcp/22", info["ports"])
        self.assertIn("tcp/80", info["ports"])
        self.assertIn("tcp/443", info["ports"])

    def test_add_note(self):
        self.profile.add_note("192.168.1.1", "Test note")
        info = self.profile.get_target("192.168.1.1")
        self.assertIn("Test note", info["notes"])


if __name__ == "__main__":
    unittest.main()
