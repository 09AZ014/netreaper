"""
NetReaper - Tests for core/watch.py
Author: 09azo14 | License: MIT
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import watch  # noqa: E402
from core.snapshot import build_snapshot  # noqa: E402
from modules import diff  # noqa: E402

NMAP_BASELINE = """\
Nmap scan report for 192.168.1.10
Host is up (0.001s latency).
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2
"""

NMAP_CHANGED = """\
Nmap scan report for 192.168.1.10
Host is up (0.001s latency).
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 9.0
3306/tcp open  mysql   MySQL 8.0

Nmap scan report for 192.168.1.11
Host is up (0.002s latency).
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache 2.4
"""

NIKTO_BASELINE = """\
- Nikto v2.5.0
+ Target IP:          192.168.1.20
+ Target Hostname:    web.local
+ Server: Apache/2.4.41
+ /admin/: Admin login page found.
+ 7913 requests: 0 error(s) and 2 item(s) reported
"""

NIKTO_CHANGED = """\
- Nikto v2.5.0
+ Target IP:          192.168.1.20
+ Target Hostname:    web.local
+ Server: Apache/2.4.41
+ /admin/: Admin login page found.
+ /backup/: Directory indexing enabled.
+ 8120 requests: 0 error(s) and 3 item(s) reported
"""


class FakeLogger:
    """Minimal stand-in for SessionLogger used by watch mode."""

    def __init__(self):
        self.commands = []
        self.reports = []

    def log_command(self, module, command, output, target=""):
        self.commands.append({
            "module": module,
            "command": command,
            "output": output,
            "target": target,
        })

    def save_report(self, name, content, fmt="txt"):
        self.reports.append((name, content))
        return name

    def close(self):
        pass


class TestAvailableActions(unittest.TestCase):
    def test_recon_actions(self):
        actions = watch.available_actions("recon")
        self.assertIn("ping_sweep", actions)
        self.assertEqual(actions, sorted(actions))

    def test_nmap_actions(self):
        self.assertIn("os_detect", watch.available_actions("nmap"))

    def test_web_actions(self):
        self.assertIn("nikto", watch.available_actions("web"))

    def test_vuln_actions(self):
        self.assertIn("nmap_vuln", watch.available_actions("vuln"))

    def test_all_four_modules_are_watchable(self):
        self.assertEqual(
            sorted(watch.WATCH_MODULES), ["nmap", "recon", "vuln", "web"]
        )


class TestRunScanSignatures(unittest.TestCase):
    """Each module has its own run() signature and must be called correctly."""

    def test_recon_receives_profile(self):
        sentinel = object()
        with mock.patch("modules.recon.run") as run_mock:
            watch._run_scan("recon", "ping_sweep", "t", sentinel, profile="P")
        run_mock.assert_called_once_with("ping_sweep", "t", sentinel, "P")

    def test_nmap_receives_profile(self):
        sentinel = object()
        with mock.patch("modules.nmap_scan.run") as run_mock:
            watch._run_scan("nmap", "fast_ports", "t", sentinel, profile="P")
        run_mock.assert_called_once_with("fast_ports", "t", sentinel, "P")

    def test_web_does_not_receive_profile(self):
        sentinel = object()
        with mock.patch("modules.web.run") as run_mock:
            watch._run_scan("web", "nikto", "t", sentinel, profile="P")
        run_mock.assert_called_once_with("nikto", "t", sentinel)

    def test_vuln_does_not_receive_profile(self):
        sentinel = object()
        with mock.patch("modules.vuln.run") as run_mock:
            watch._run_scan("vuln", "nmap_vuln", "t", sentinel)
        run_mock.assert_called_once_with("nmap_vuln", "t", sentinel)


class TestResolveInterval(unittest.TestCase):
    def test_explicit_value(self):
        self.assertEqual(watch.resolve_interval(45), 45)

    def test_string_value(self):
        self.assertEqual(watch.resolve_interval("60"), 60)

    def test_rejects_zero_and_negative(self):
        self.assertEqual(watch.resolve_interval(0), watch.DEFAULT_INTERVAL)
        self.assertEqual(watch.resolve_interval(-5), watch.DEFAULT_INTERVAL)

    def test_rejects_non_numeric(self):
        self.assertEqual(watch.resolve_interval("soon"), watch.DEFAULT_INTERVAL)

    def test_defaults_from_config(self):
        with mock.patch("core.watch.get_config") as get_cfg:
            get_cfg.return_value.get.return_value = 120
            self.assertEqual(watch.resolve_interval(), 120)


class TestLineNormalisation(unittest.TestCase):
    def test_strips_ansi_and_collapses_whitespace(self):
        self.assertEqual(watch.normalise_line("\x1b[32m+  hello\x1b[0m   world"), "+ hello world")

    def test_strips_timestamps_and_durations(self):
        line = watch.normalise_line("2024-01-01 10:00:00 scan done (1.23s)")
        self.assertEqual(line, "scan done")

    def test_strips_http_dates(self):
        self.assertEqual(watch.normalise_line("Date: Mon, 01 Jan 2024 10:00:00 GMT"), "Date:")


class TestFindingExtraction(unittest.TestCase):
    def test_extracts_findings_and_drops_noise(self):
        findings = watch.extract_findings(NIKTO_BASELINE)
        self.assertTrue(any("/admin/" in f for f in findings))
        self.assertFalse(any("requests:" in f for f in findings))

    def test_volatile_headers_are_ignored(self):
        output = "Date: Mon, 01 Jan 2024 10:00:00 GMT\nServer: nginx\nETag: abc"
        findings = watch.extract_findings(output)
        self.assertEqual(findings, ["Server: nginx"])

    def test_separators_and_blank_lines_are_ignored(self):
        output = "=====\n\n---\nreal finding\n"
        self.assertEqual(watch.extract_findings(output), ["real finding"])

    def test_findings_are_deduplicated_and_sorted(self):
        output = "beta\nalpha\nbeta\n"
        self.assertEqual(watch.extract_findings(output), ["alpha", "beta"])

    def test_empty_output_yields_no_findings(self):
        self.assertEqual(watch.extract_findings(""), [])

    def test_is_noise_classifier(self):
        self.assertTrue(watch.is_noise(""))
        self.assertTrue(watch.is_noise("=" * 20))
        self.assertTrue(watch.is_noise("+ 7913 requests: 0 error(s) and 2 item(s) reported"))
        self.assertFalse(watch.is_noise("+ /admin/: Admin login page found."))


class TestFindingsComparison(unittest.TestCase):
    def test_detects_added_and_removed(self):
        result = watch.diff_findings(["a", "b"], ["b", "c"])
        self.assertEqual(result["findings_added"], ["c"])
        self.assertEqual(result["findings_removed"], ["a"])

    def test_identical_findings_are_empty(self):
        result = watch.diff_findings(["a"], ["a"])
        self.assertTrue(watch.is_empty_change(result))
        self.assertTrue(watch.is_findings_diff(result))

    def test_compare_states_prefers_semantic_when_hosts_present(self):
        previous = build_snapshot(NMAP_BASELINE)
        current = build_snapshot(NMAP_CHANGED)
        result = watch.compare_states(previous, current)
        self.assertFalse(watch.is_findings_diff(result))
        self.assertIn("192.168.1.11", result["hosts_added"])

    def test_compare_states_uses_findings_when_no_hosts(self):
        previous = {"hosts": {}, "findings": ["a"]}
        current = {"hosts": {}, "findings": ["b"]}
        result = watch.compare_states(previous, current)
        self.assertTrue(watch.is_findings_diff(result))
        self.assertEqual(result["findings_added"], ["b"])

    def test_format_change_semantic(self):
        result = watch.compare_states(build_snapshot(NMAP_BASELINE), build_snapshot(NMAP_CHANGED))
        self.assertIn("New host discovered", watch.format_change(result))

    def test_format_change_findings(self):
        result = watch.diff_findings([], ["+ /backup/: Directory indexing enabled."])
        text = watch.format_change(result)
        self.assertIn("[+] + /backup/", text)

    def test_format_change_empty_findings(self):
        self.assertIn("No changes", watch.format_change(watch.diff_findings([], [])))


class TestCaptureState(unittest.TestCase):
    def test_captures_hosts_and_findings(self):
        logger = FakeLogger()

        def fake_scan(command, action, target, log, profile=None):
            log.log_command("recon", "nmap -sn x", NMAP_BASELINE, target)

        with mock.patch("core.watch._run_scan", side_effect=fake_scan):
            state = watch.capture_state("recon", "ping_sweep", "192.168.1.10", logger)

        self.assertIn("192.168.1.10", state["hosts"])
        self.assertTrue(state["findings"])

    def test_only_new_output_is_used(self):
        logger = FakeLogger()
        logger.log_command("recon", "old", NMAP_CHANGED, "")

        def fake_scan(command, action, target, log, profile=None):
            log.log_command("recon", "new", NMAP_BASELINE, target)

        with mock.patch("core.watch._run_scan", side_effect=fake_scan):
            state = watch.capture_state("recon", "ping_sweep", "192.168.1.10", logger)

        self.assertEqual(list(state["hosts"]), ["192.168.1.10"])

    def test_no_new_output_yields_empty_state(self):
        logger = FakeLogger()
        with mock.patch("core.watch._run_scan", return_value=None):
            state = watch.capture_state("recon", "ping_sweep", "x", logger)
        self.assertEqual(state["hosts"], {})
        self.assertEqual(state["findings"], [])
        self.assertFalse(watch.has_state(state))


class TestSendWebhook(unittest.TestCase):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def test_empty_url_returns_false(self):
        self.assertFalse(watch.send_webhook("", {"a": 1}))

    def test_successful_post(self):
        target = "core.watch.urllib.request.urlopen"
        with mock.patch(target, return_value=self.FakeResponse()):
            self.assertTrue(watch.send_webhook("http://example.test/hook", {"a": 1}))

    def test_failed_post_returns_false(self):
        target = "core.watch.urllib.request.urlopen"
        with mock.patch(target, side_effect=OSError("boom")):
            self.assertFalse(watch.send_webhook("http://example.test/hook", {"a": 1}))


class TestAlerts(unittest.TestCase):
    def _semantic_result(self):
        return diff.diff_snapshots(
            build_snapshot(NMAP_BASELINE), build_snapshot(NMAP_CHANGED)
        )

    def test_build_alert_structure(self):
        payload = watch.build_alert(self._semantic_result(), "192.168.1.10", 3)
        self.assertEqual(payload["event"], "scan_change")
        self.assertEqual(payload["kind"], "semantic")
        self.assertEqual(payload["target"], "192.168.1.10")
        self.assertEqual(payload["iteration"], 3)
        self.assertIn("192.168.1.11", payload["changes"])

    def test_build_alert_for_findings(self):
        payload = watch.build_alert(watch.diff_findings([], ["new"]), "10.0.0.1", 1)
        self.assertEqual(payload["kind"], "findings")
        self.assertIn("[+] new", payload["changes"])

    def test_emit_alert_saves_report_and_posts_webhook(self):
        logger = FakeLogger()
        with mock.patch("core.watch.send_webhook", return_value=True) as hook:
            payload = watch.emit_alert(
                self._semantic_result(), "192.168.1.10", 2, logger, "http://example.test/hook"
            )
        self.assertEqual(len(logger.reports), 1)
        self.assertIn("watch_change_run2", logger.reports[0][0])
        hook.assert_called_once()
        self.assertEqual(payload["target"], "192.168.1.10")

    def test_emit_alert_for_findings_diff(self):
        logger = FakeLogger()
        result = watch.diff_findings([], ["+ /backup/: Directory indexing enabled."])
        payload = watch.emit_alert(result, "10.0.0.1", 1, logger, None)
        self.assertEqual(payload["kind"], "findings")
        self.assertIn("backup", logger.reports[0][1])

    def test_emit_alert_without_webhook_does_not_call_it(self):
        with mock.patch("core.watch.send_webhook") as hook:
            watch.emit_alert(self._semantic_result(), "192.168.1.10", 1, FakeLogger(), None)
        hook.assert_not_called()


class TestWatchLoop(unittest.TestCase):
    def _run(self, states, max_iterations=2, webhook=""):
        seq = iter(states)
        slept = []
        capture = mock.patch("core.watch.capture_state", side_effect=lambda *a, **k: next(seq))
        with capture:
            with mock.patch("core.watch.emit_alert") as alert:
                changes = watch.run(
                    "recon", "ping_sweep", "192.168.1.10", FakeLogger(),
                    interval=7, max_iterations=max_iterations,
                    webhook=webhook, sleep_fn=slept.append,
                )
        return changes, alert, slept

    def test_detects_semantic_change_and_alerts(self):
        changes, alert, slept = self._run([build_snapshot(NMAP_BASELINE),
                                           build_snapshot(NMAP_CHANGED)])
        self.assertEqual(changes, 1)
        self.assertEqual(alert.call_count, 1)
        self.assertEqual(slept, [7])

    def test_detects_findings_change_and_alerts(self):
        baseline = {"hosts": {}, "findings": watch.extract_findings(NIKTO_BASELINE)}
        changed = {"hosts": {}, "findings": watch.extract_findings(NIKTO_CHANGED)}
        changes, alert, _ = self._run([baseline, changed])
        self.assertEqual(changes, 1)
        self.assertEqual(alert.call_count, 1)

    def test_unchanged_findings_do_not_alert(self):
        findings = watch.extract_findings(NIKTO_BASELINE)
        changes, alert, _ = self._run([{"hosts": {}, "findings": findings},
                                       {"hosts": {}, "findings": findings}])
        self.assertEqual(changes, 0)
        alert.assert_not_called()

    def test_no_change_does_not_alert(self):
        changes, alert, _ = self._run([build_snapshot(NMAP_BASELINE),
                                       build_snapshot(NMAP_BASELINE)])
        self.assertEqual(changes, 0)
        alert.assert_not_called()

    def test_unparseable_run_is_skipped(self):
        changes, alert, _ = self._run([build_snapshot("nothing here"),
                                       build_snapshot("still nothing")])
        self.assertEqual(changes, 0)
        alert.assert_not_called()

    def test_limit_of_one_run_never_compares(self):
        changes, alert, slept = self._run([build_snapshot(NMAP_BASELINE)], max_iterations=1)
        self.assertEqual(changes, 0)
        alert.assert_not_called()
        self.assertEqual(slept, [])

    def test_unknown_command_returns_zero(self):
        with mock.patch("core.watch.capture_state") as capture:
            self.assertEqual(watch.run("bogus", "x", "y", FakeLogger()), 0)
        capture.assert_not_called()

    def test_interrupt_stops_loop(self):
        seq = iter([build_snapshot(NMAP_BASELINE), build_snapshot(NMAP_BASELINE)])
        capture = mock.patch("core.watch.capture_state", side_effect=lambda *a, **k: next(seq))
        with capture:
            with mock.patch("core.watch.emit_alert"):
                changes = watch.run(
                    "recon", "ping_sweep", "192.168.1.10", FakeLogger(),
                    interval=5, webhook="",
                    sleep_fn=mock.Mock(side_effect=KeyboardInterrupt),
                )
        self.assertEqual(changes, 0)


if __name__ == "__main__":
    unittest.main()
