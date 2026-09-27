"""Hermetic release-tag decisions and non-failing warning reporting."""
from contextlib import redirect_stdout
import importlib.util
import io
import subprocess
import unittest
from unittest.mock import Mock, call

from support import ROOT

spec = importlib.util.spec_from_file_location("release_checker", ROOT / "skills/check_skills.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def result(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class ReleaseTagTests(unittest.TestCase):
    def test_present_and_ancestor(self):
        git = Mock(side_effect=[result(), result(stdout="abc123\n"), result()])
        self.assertEqual(checker.release_tag_status("1.6.0", git),
                         ("PASS", "skills/v1.6.0 is HEAD or an ancestor of HEAD"))
        self.assertEqual(git.call_args_list, [
            call("show-ref", "--verify", "--quiet", "refs/tags/skills/v1.6.0"),
            call("rev-parse", "--verify", "refs/tags/skills/v1.6.0^{commit}"),
            call("merge-base", "--is-ancestor", "abc123", "HEAD"),
        ])

    def test_absent_or_unfetched(self):
        git = Mock(return_value=result(1))
        status, observed = checker.release_tag_status("1.6.0", git)
        self.assertEqual(status, "WARN")
        self.assertIn("absent locally", observed)
        self.assertIn("tags were not fetched", observed)
        self.assertEqual(git.call_count, 1)

    def test_not_ancestor(self):
        git = Mock(side_effect=[result(), result(stdout="def456\n"), result(1)])
        status, observed = checker.release_tag_status("1.6.0", git)
        self.assertEqual(status, "WARN")
        self.assertIn("def456 is not an ancestor of HEAD", observed)

    def test_git_errors(self):
        for responses in ([result(128, stderr="not a repository")],
                          [result(), result(128, stderr="not a commit")],
                          [result(), result(stdout="abc123"), result(128, stderr="bad HEAD")]):
            with self.subTest(responses=responses):
                status, observed = checker.release_tag_status("1.6.0", Mock(side_effect=responses))
                self.assertEqual(status, "WARN")
                self.assertIn("check could not run", observed)
                self.assertIn(responses[-1].stderr, observed)

    def test_git_unavailable(self):
        status, observed = checker.release_tag_status("1.6.0", Mock(side_effect=FileNotFoundError("git")))
        self.assertEqual(status, "WARN")
        self.assertIn("check could not run: git", observed)

    def test_warning_does_not_fail(self):
        report = checker.Reporter()
        output = io.StringIO()
        with redirect_stdout(output):
            report.warn("release tag", "absent", "skills/v1.6.0", "See MAINTAINING.md.")
        self.assertEqual((report.checks, report.failed, report.warnings), (1, 0, 1))
        self.assertEqual(output.getvalue(),
                         "WARN release tag: observed=absent, expected=skills/v1.6.0; See MAINTAINING.md.\n")
