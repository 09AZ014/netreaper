"""
NetReaper - Tests for the non-interactive CLI (netreaper.py)
Author: 09azo14 | License: MIT
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

import netreaper  # noqa: E402


def _args(*argv):
    return netreaper.parse_args(list(argv))


class TestParseArgs(unittest.TestCase):
    def test_recon_subcommand(self):
        args = _args("recon", "ping_sweep", "-t", "10.0.0.0/24")
        self.assertEqual(args.command, "recon")
        self.assertEqual(args.action, "ping_sweep")
        self.assertEqual(args.target, "10.0.0.0/24")

    def test_long_target_flag(self):
        args = _args("web", "nikto", "--target", "192.168.1.5")
        self.assertEqual(args.target, "192.168.1.5")

    def test_vuln_subcommand(self):
        args = _args("vuln", "nmap_vuln", "-t", "host")
        self.assertEqual((args.command, args.action), ("vuln", "nmap_vuln"))

    def test_list_flag(self):
        self.assertTrue(_args("--list").list_actions)

    def test_version_exits(self):
        with self.assertRaises(SystemExit):
            _args("--version")

    def test_top_level_target_default_is_none(self):
        self.assertIsNone(_args().target)

    def test_subcommand_without_action(self):
        self.assertIsNone(_args("recon").action)

    def test_install_flag_before_subcommand_is_kept(self):
        args = _args("--install", "recon", "ping_sweep", "-t", "x")
        self.assertTrue(args.install)

    def test_install_flag_on_subcommand(self):
        args = _args("recon", "ping_sweep", "-t", "x", "--install")
        self.assertTrue(args.install)

    def test_watch_subcommand(self):
        args = _args(
            "watch", "--module", "nmap", "--action", "os_detect",
            "-t", "10.0.0.9", "--interval", "30", "--count", "3",
        )
        self.assertEqual(args.command, "watch")
        self.assertEqual(args.module, "nmap")
        self.assertEqual(args.action, "os_detect")
        self.assertEqual(args.target, "10.0.0.9")
        self.assertEqual(args.interval, 30)
        self.assertEqual(args.count, 3)

    def test_watch_defaults_to_recon_module(self):
        args = _args("watch", "--action", "ping_sweep", "-t", "x")
        self.assertEqual(args.module, "recon")
        self.assertEqual(args.count, 0)
        self.assertIsNone(args.interval)

    def test_watch_requires_action(self):
        with self.assertRaises(SystemExit):
            _args("watch")

    def test_watch_accepts_web_and_vuln_modules(self):
        self.assertEqual(_args("watch", "--action", "nikto", "--module", "web").module, "web")
        vuln = _args("watch", "--action", "nmap_vuln", "--module", "vuln")
        self.assertEqual(vuln.module, "vuln")

    def test_watch_rejects_unknown_module(self):
        with self.assertRaises(SystemExit):
            _args("watch", "--action", "nikto", "--module", "bogus")


class TestAvailableActions(unittest.TestCase):
    def test_recon_actions(self):
        actions = netreaper.available_actions("recon")
        self.assertIn("ping_sweep", actions)
        self.assertIn("arp_scan", actions)
        self.assertEqual(actions, sorted(actions))

    def test_web_actions(self):
        self.assertIn("gobuster", netreaper.available_actions("web"))

    def test_vuln_actions(self):
        self.assertIn("nmap_vuln", netreaper.available_actions("vuln"))

    def test_watch_available_actions(self):
        self.assertIn("ping_sweep", netreaper.watch_available_actions("recon"))
        self.assertIn("os_detect", netreaper.watch_available_actions("nmap"))
        self.assertIn("nikto", netreaper.watch_available_actions("web"))
        self.assertIn("nmap_vuln", netreaper.watch_available_actions("vuln"))

    def test_print_available_actions_runs(self):
        netreaper.print_available_actions()


class TestResolveTarget(unittest.TestCase):
    def test_prefers_cli_flag(self):
        args = _args("recon", "ping_sweep", "-t", "10.1.1.1")
        with mock.patch("core.config.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = "9.9.9.9"
            self.assertEqual(netreaper.resolve_target(args), "10.1.1.1")

    def test_falls_back_to_config(self):
        args = _args("recon", "ping_sweep")
        with mock.patch("core.config.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = "9.9.9.9"
            self.assertEqual(netreaper.resolve_target(args), "9.9.9.9")

    def test_empty_when_unset(self):
        args = _args("recon", "ping_sweep")
        with mock.patch("core.config.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = ""
            self.assertEqual(netreaper.resolve_target(args), "")


class TestRunCliCommand(unittest.TestCase):
    def test_missing_action_returns_usage_error(self):
        self.assertEqual(netreaper.run_cli_command(_args("recon")), 2)

    def test_unknown_action_returns_usage_error(self):
        args = _args("web", "not_a_real_action", "-t", "x")
        self.assertEqual(netreaper.run_cli_command(args), 2)

    def test_missing_target_returns_usage_error(self):
        args = _args("vuln", "lynis")
        with mock.patch("core.config.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = ""
            self.assertEqual(netreaper.run_cli_command(args), 2)

    def test_dispatches_to_recon_module(self):
        args = _args("recon", "ping_sweep", "-t", "10.0.0.0/24")
        logger = mock.MagicMock()
        with mock.patch("modules.recon.run") as run_mock, \
                mock.patch("core.profile.TargetProfile"):
            rc = netreaper.run_cli_command(args, logger=logger)
        self.assertEqual(rc, 0)
        run_mock.assert_called_once()
        self.assertEqual(run_mock.call_args[0][0], "ping_sweep")
        self.assertEqual(run_mock.call_args[0][1], "10.0.0.0/24")

    def test_dispatches_to_web_module(self):
        args = _args("web", "headers", "-t", "10.0.0.5")
        logger = mock.MagicMock()
        with mock.patch("modules.web.run") as run_mock:
            rc = netreaper.run_cli_command(args, logger=logger)
        self.assertEqual(rc, 0)
        run_mock.assert_called_once_with("headers", "10.0.0.5", logger)

    def test_dispatches_to_vuln_module(self):
        args = _args("vuln", "nmap_vuln", "-t", "10.0.0.6")
        logger = mock.MagicMock()
        with mock.patch("modules.vuln.run") as run_mock:
            rc = netreaper.run_cli_command(args, logger=logger)
        self.assertEqual(rc, 0)
        run_mock.assert_called_once_with("nmap_vuln", "10.0.0.6", logger)

    def test_interactive_action_reports_helpfully(self):
        args = _args("web", "sqlmap", "-t", "10.0.0.7")
        logger = mock.MagicMock()
        with mock.patch("modules.web.run", side_effect=EOFError):
            rc = netreaper.run_cli_command(args, logger=logger)
        self.assertEqual(rc, 2)


class TestRunWatchCommand(unittest.TestCase):
    def test_unknown_action_returns_usage_error(self):
        args = _args("watch", "--module", "recon", "--action", "bogus", "-t", "1.1.1.1")
        self.assertEqual(netreaper.run_watch_command(args), 2)

    def test_missing_target_returns_usage_error(self):
        args = _args("watch", "--module", "recon", "--action", "ping_sweep")
        with mock.patch("core.config.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = ""
            self.assertEqual(netreaper.run_watch_command(args), 2)

    def test_dispatches_web_watch(self):
        args = _args("watch", "--module", "web", "--action", "nikto", "-t", "10.0.0.2")
        with mock.patch("core.watch.run") as run_mock:
            with mock.patch("core.logger.SessionLogger"):
                with mock.patch("core.profile.TargetProfile"):
                    rc = netreaper.run_watch_command(args)
        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_args[0][:3], ("web", "nikto", "10.0.0.2"))

    def test_web_watch_unknown_action(self):
        args = _args("watch", "--module", "web", "--action", "bogus", "-t", "1.1.1.1")
        self.assertEqual(netreaper.run_watch_command(args), 2)

    def test_interactive_watch_action_reports_helpfully(self):
        args = _args("watch", "--module", "web", "--action", "gobuster", "-t", "1.1.1.1")
        with mock.patch("core.watch.run", side_effect=EOFError):
            with mock.patch("core.logger.SessionLogger"):
                with mock.patch("core.profile.TargetProfile"):
                    rc = netreaper.run_watch_command(args)
        self.assertEqual(rc, 2)

    def test_dispatches_to_watch_run(self):
        args = _args(
            "watch", "--module", "recon", "--action", "ping_sweep",
            "-t", "10.0.0.1", "--interval", "15", "--count", "2",
        )
        with mock.patch("core.watch.run") as run_mock:
            with mock.patch("core.logger.SessionLogger") as logger_cls:
                with mock.patch("core.profile.TargetProfile"):
                    rc = netreaper.run_watch_command(args)
        self.assertEqual(rc, 0)
        run_mock.assert_called_once()
        self.assertEqual(run_mock.call_args[0][:3], ("recon", "ping_sweep", "10.0.0.1"))
        self.assertEqual(run_mock.call_args[1]["interval"], 15)
        self.assertEqual(run_mock.call_args[1]["max_iterations"], 2)
        logger_cls.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
