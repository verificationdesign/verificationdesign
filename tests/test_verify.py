"""Verifier checks against isolated, committed, substitute-topic repositories."""

from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research_tools.profile import load_profile
from research_tools import verify


REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
URLS = ["https://arxiv.org/abs/2601.00001", "https://arxiv.org/abs/2601.00002"]


def fixture(root):
    for name in ("reviewed", "triage", "scouts"):
        (root / "research" / name).mkdir(parents=True)
    raw = json.loads((FIXTURES / "config-sample.json").read_text())
    raw["principles"] = {"a": "Seasonal sampling", "b": "Habitat coverage", "c": "Ocean currents"}
    (root / "research/scouts/config.json").write_text(json.dumps(raw))
    citations = [f"[arXiv:2601.0000{i + 1}]({url})" for i, url in enumerate(URLS)]
    (root / "marine-notes.md").write_text(
        "# Marine notes\n\n" + "\n".join(f"### {i}. {title}" for i, title in enumerate(raw["principles"].values(), 1))
        + "\n\n" + " and ".join(citations) + "\n\n[Sampling](#1-seasonal-sampling)\n\n## References\n\n"
        + "| Source | Notes |\n| --- | --- |\n" + "".join(f"| {c} | Evidence |\n" for c in citations))
    for i, url in enumerate(URLS):
        (root / f"research/reviewed/source-{i}.md").write_text(
            f"# Source {i}\nReviewed: 2026-09-11\nReviewer: Fixture\nSource: {url}\n"
            "Evidence grade: C\nGrade confidence: medium\n\n## Limitations\nNarrow coverage.\n"
            "\n## Claims Needing Human Review\nAll claims.\n")
    (root / "research/reviewed/LEGACY-CITATIONS.md").write_text("# Legacy citations\n")
    shutil.copyfile(FIXTURES / "triage-sample.md", root / "research/triage/sample.md")
    (root / "research/synthesis.md").write_text("# Synthesis\n\n2026-09-11 update: Source: fixture observations.\nA retained observation.\n")
    for name in ("README.md", "AGENTS.md", "research/link-confirmations.txt"):
        (root / name).write_text("")
    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "Fixture baseline")
    return load_profile(root / "research/scouts/config.json")


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = fixture(self.root)

    def run_checks(self, **kwargs):
        options = dict(skip_links=True, include_scout_links=False, base_ref="HEAD")
        options.update(kwargs)
        with patch("urllib.request.urlopen", side_effect=AssertionError("live access")):
            return verify.run(self.root, self.profile, **options)

    def edit(self, path, before, after):
        file = self.root / path
        text = file.read_text()
        self.assertIn(before, text)
        file.write_text(text.replace(before, after))

    def assert_failure(self, name, detail):
        failed = [c for c in self.run_checks() if not c.ok]
        self.assertEqual([c.name for c in failed], [name])
        self.assertTrue(any(detail in item for item in failed[0].details), failed[0])

    def test_custom_profile_reaches_scout_config_check(self):
        default = self.root / "research/scouts/config.json"
        custom = self.root / "custom-profile.json"
        raw = json.loads(default.read_text())
        raw["keyword_groups"] = {}
        custom.write_text(json.dumps(raw))
        self.assertTrue(all(c.ok for c in self.run_checks()), "default profile must still pass")
        with patch("urllib.request.urlopen", side_effect=AssertionError("live access")):
            checks = verify.run(self.root, load_profile(custom), skip_links=True,
                                include_scout_links=False, base_ref="HEAD", profile_path=custom)
        failed = [c for c in checks if not c.ok]
        self.assertEqual([c.name for c in failed], ["scout config / query shape"])
        self.assertTrue(any("keyword_groups block missing or empty" in d for d in failed[0].details), failed[0])
        checks = verify.run(self.root, self.profile, skip_links=True, include_scout_links=False,
                            base_ref="HEAD", profile_path=self.root / "absent.json")
        failed = [c for c in checks if not c.ok]
        self.assertEqual([(c.name, c.observed) for c in failed], [("scout config / query shape", "profile missing")])

    def test_positive_counts(self):
        checks = self.run_checks()
        self.assertEqual(len(checks), 12)
        self.assertTrue(all(c.ok for c in checks), checks)
        self.assertEqual([c.observed for c in checks], [
            "2 inline citation labels; 2 reference labels; 0 imbalances",
            "9 parser cases checked; 0 failures",
            "2 canonical citation labels; 2 reviewed-note labels; 0 legacy labels; 0 missing reviewed notes",
            "3 numbered principles; 5 anchors; 0 failures",
            "marine-notes.md: 0 update note blocks inspected; 0 failures",
            "research/synthesis.md: 1 update note blocks inspected; 0 failures",
            "2 reviewed source notes inspected; 0 failures",
            "1 triage notes inspected; 3 candidates inspected; 0 failures",
            "research/synthesis.md: 0 deleted non-blank lines without an allowed replacement in git diff against HEAD",
            "0 legacy labels; ceiling 13; 0 added labels in git diff against HEAD",
            "2 categories; 2 groups; 2 anchors; 3 topic phrases; 2 dry-run requests",
            "3 profile principles; 3 canonical headings; 0 failures",
        ])

    def test_orphan_inline(self):
        self.edit("marine-notes.md", f"| [arXiv:2601.00001]({URLS[0]}) | Evidence |\n", "")
        self.assert_failure("citation/reference balance", "inline citation without reference row: arXiv:2601.00001")

    def test_orphan_reference(self):
        self.edit("marine-notes.md", f"[arXiv:2601.00001]({URLS[0]}) and ", "")
        self.assert_failure("citation/reference balance", "reference row not cited inline: arXiv:2601.00001")

    def test_missing_reviewed_source(self):
        (self.root / "research/reviewed/source-0.md").unlink()
        self.assert_failure("citation reviewed-note provenance", "canonical citation lacks reviewed note source: arXiv:2601.00001")

    def test_numbering_gap(self):
        self.edit("marine-notes.md", "### 3.", "### 4.")
        self.assert_failure("format / anchor lint", "numbering observed [1, 2, 4], expected [1, 2, 3]")

    def test_broken_anchor(self):
        self.edit("marine-notes.md", "(#1-seasonal-sampling)", "(#missing)")
        self.assert_failure("format / anchor lint", "unresolved internal anchor: #missing")

    def test_dated_update_without_source(self):
        # Append so this isolates provenance without violating append-only policy.
        with (self.root / "research/synthesis.md").open("a") as file:
            file.write("\n2026-09-11 update: Unattributed observation.\n")
        self.assert_failure("provenance", "update note does not name a source")

    def test_undated_update_without_source(self):
        # An "Update:" marker without a date is still an update note and needs a source.
        with (self.root / "research/synthesis.md").open("a") as file:
            file.write("\nUpdate: Unattributed observation.\n")
        self.assert_failure("provenance", "update note does not name a source")

    def test_undated_update_with_source_passes(self):
        with (self.root / "research/synthesis.md").open("a") as file:
            file.write("\n> **Update**: Attributed observation. Source: [arXiv:2601.00001](https://arxiv.org/abs/2601.00001)\n")
        checks = self.run_checks()
        self.assertTrue(all(c.ok for c in checks), checks)
        self.assertEqual(checks[5].observed,
                         "research/synthesis.md: 2 update note blocks inspected; 0 failures")

    def test_prose_mentioning_update_is_not_a_note(self):
        with (self.root / "research/synthesis.md").open("a") as file:
            file.write("\nThe model update cadence is unrelated to provenance.\n")
        checks = self.run_checks()
        self.assertTrue(all(c.ok for c in checks), checks)
        self.assertEqual(checks[5].observed,
                         "research/synthesis.md: 1 update note blocks inspected; 0 failures")

    def test_review_missing_field(self):
        self.edit("research/reviewed/source-0.md", "Reviewer: Fixture\n", "")
        self.assert_failure("review note metadata", "source-0.md missing or invalid Reviewer")

    def test_triage_missing_decision(self):
        self.edit("research/triage/sample.md", "Decision: promote\n", "")
        self.assert_failure("triage note metadata", "expected decision")

    def test_triage_invalid_label(self):
        self.edit("research/triage/sample.md", "Initial label: ignore", "Initial label: invalid")
        self.assert_failure("triage note metadata", "missing or invalid Initial label")

    def test_synthesis_deleted_line(self):
        self.edit("research/synthesis.md", "A retained observation.\n", "")
        self.assert_failure("append-not-overwrite", "-A retained observation.")

    def test_new_legacy_label(self):
        with (self.root / "research/reviewed/LEGACY-CITATIONS.md").open("a") as file:
            file.write("[arXiv:2601.99999](https://arxiv.org/abs/2601.99999)\n")
        self.assert_failure("legacy citation bridge", "added legacy labels are not allowed: arXiv:2601.99999")

    def test_bad_scout_category(self):
        self.edit("research/scouts/config.json", '"q-bio.PE": "populations and evolution"', '"q-bio.PE": 42')
        self.assert_failure("scout config / query shape", "description is not a string: 42")

    def test_mismatching_principle(self):
        self.profile = replace(self.profile, principles={**self.profile.principles, "c": "Salinity"})
        self.assert_failure("principles match canonical doc", "title observed 'Ocean currents', expected 'Salinity'")

    def test_principle_count(self):
        self.profile = replace(self.profile, principles={"a": "Seasonal sampling"})
        self.assert_failure("principles match canonical doc", "count observed 3, expected 1")

    def test_links(self):
        requested = []
        class Response:
            def __init__(self, status): self.status = status
            def __enter__(self): return self
            def __exit__(self, *args): pass
        def fetch(request, timeout):
            self.assertEqual(timeout, 15)
            requested.append(request.full_url)
            return Response(200)
        checks = self.run_checks(skip_links=False, fetch=fetch)
        self.assertTrue(all(c.ok for c in checks), checks)
        expected = set(URLS) | {"https://arxiv.org/abs/2605.30244", "https://arxiv.org/abs/2605.29711", "https://arxiv.org/abs/2605.29277"}
        self.assertEqual(set(requested), expected)
        self.assertEqual(len(requested), 5)
        self.assertEqual(checks[0].observed, "5 unique URLs checked; 0 manually confirmed; 0 failures")
        def bad_fetch(request, timeout):
            return Response(404 if request.full_url == URLS[0] else 200)
        checks = self.run_checks(skip_links=False, fetch=bad_fetch)
        self.assertEqual([c.name for c in checks if not c.ok], ["link liveness"])
        self.assertEqual(checks[0].details, [URLS[0] + " -> HTTP 404"])
        # A confirmation is consulted only after the fetch fails, so confirmed URLs are still re-tested.
        (self.root / "research/link-confirmations.txt").write_text(f"2026-09-11 {URLS[0]} -- Checked manually\n")
        requested.clear()
        def bad_fetch_recording(request, timeout):
            requested.append(request.full_url)
            return Response(404 if request.full_url == URLS[0] else 200)
        checks = self.run_checks(skip_links=False, fetch=bad_fetch_recording)
        self.assertIn(URLS[0], requested)
        self.assertTrue(checks[0].ok, checks[0])
        self.assertEqual(checks[0].observed, "5 unique URLs checked; 1 manually confirmed; 0 failures")
        checks = self.run_checks(skip_links=False, fetch=fetch)
        self.assertEqual(checks[0].observed, "5 unique URLs checked; 0 manually confirmed; 0 failures")

    def test_skip_links_never_fetches(self):
        def guard(*args, **kwargs):
            raise AssertionError("live access")
        with self.assertRaisesRegex(AssertionError, "live access"):
            guard()
        checks = self.run_checks(fetch=guard)
        self.assertTrue(all(c.ok for c in checks), checks)
        # url_ok preserves the old exception-to-failure behavior; prove the guard is used.
        self.assertEqual(verify.url_ok(URLS[0], fetch=guard), (False, "live access"))

    def test_cli(self):
        result = subprocess.run([sys.executable, "-m", "research_tools", "verify", "--skip-links", "--base-ref", "HEAD"],
                                cwd=REPO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(len(result.stdout.splitlines()), 12)
        self.assertTrue(all(line.startswith("[PASS]") for line in result.stdout.splitlines()))

    def test_cli_profile_flag_is_validated(self):
        raw = json.loads((REPO / "research/scouts/config.json").read_text())
        raw["keyword_groups"] = {}
        custom = self.root / "profile.json"
        custom.write_text(json.dumps(raw))
        result = subprocess.run([sys.executable, "-m", "research_tools", "verify", "--skip-links",
                                 "--base-ref", "HEAD", "--profile", str(custom)],
                                cwd=REPO, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        failed = [line for line in result.stdout.splitlines() if line.startswith("[FAIL]")]
        self.assertEqual(len(failed), 1, result.stdout)
        self.assertIn("scout config / query shape", failed[0])
        self.assertIn("keyword_groups block missing or empty", result.stdout)
