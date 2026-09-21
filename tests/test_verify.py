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

    def link_fakes(self, missing=(), api_status=None, api_body=None, page_status=None, retry_after=None):
        """Fake fetch and sleep sharing one event trace.

        The export API lists every requested id except `missing`, each at version 2. Ids must
        arrive unversioned: live API behavior for a pinned id is unverified, so the checker
        never relies on it. `api_status` maps a 1-based API request number to an HTTP error status.
        """
        events = []
        api_status, page_status = api_status or {}, page_status or {}
        headers = {"Retry-After": retry_after} if retry_after else {}
        class Response:
            def __init__(self, status, body=b""): self.status, self.body = status, body
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return self.body
        def http_error(url, status):
            error = verify.urllib.error.HTTPError(url, status, "", headers, None)
            self.addCleanup(error.close)
            return error
        def fetch(request, timeout):
            url = request.full_url
            if url.startswith(verify.ARXIV_API_URL):
                self.assertEqual(timeout, 60)
                query = verify.urllib.parse.parse_qs(verify.urllib.parse.urlsplit(url).query)
                ids = query["id_list"][0].split(",")
                self.assertEqual(query["max_results"], [str(len(ids))])
                events.append(("API", ids))
                number = sum(1 for kind, _ in events if kind == "API")
                if number in api_status:
                    raise http_error(url, api_status[number])
                if api_body is not None:
                    return Response(200, api_body)
                for requested in ids:
                    self.assertNotRegex(requested, r"v\d+$")
                entries = "".join(f"<entry><id>http://arxiv.org/abs/{i}v2</id></entry>" for i in ids if i not in missing)
                return Response(200, f'<feed xmlns="http://www.w3.org/2005/Atom"><id>q</id>{entries}</feed>'.encode())
            self.assertEqual(timeout, 15)
            events.append((request.get_method(), url))
            status = page_status.get((request.get_method(), url), page_status.get(url, 200))
            if status >= 400:
                raise http_error(url, status)
            return Response(status)
        return fetch, (lambda seconds: events.append(("sleep", seconds))), events

    def links(self, **fakes):
        fetch, sleep, events = self.link_fakes(**fakes)
        checks = self.run_checks(skip_links=False, fetch=fetch, sleep=sleep)
        self.assertEqual([c.name for c in checks if not c.ok], [] if checks[0].ok else ["link liveness"])
        return checks[0], events

    def write_links(self, urls):
        (self.root / "README.md").write_text("\n".join(f"- <{url}>" for url in urls) + "\n")

    STOP = " This is a stop, not a dead link: rerun later, do not retry now."
    FIXTURE_IDS = ["2601.00001", "2601.00002", "2605.29277", "2605.29711", "2605.30244"]

    def test_links(self):
        check, events = self.links()
        self.assertTrue(check.ok, check)
        # Five arXiv abs URLs cost one export API request and no arxiv.org page request.
        self.assertEqual(events, [("API", self.FIXTURE_IDS)])
        self.assertEqual(check.observed, "5 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 0 manually confirmed; 0 dead; 0 not checked")
        check, events = self.links(missing={"2601.00001"})
        self.assertEqual(check.details, [URLS[0] + " -> not listed by the arXiv export API"])
        # A confirmation is consulted only after the check fails, so confirmed URLs are still re-tested.
        (self.root / "research/link-confirmations.txt").write_text(f"2026-09-11 {URLS[0]} -- Checked manually\n")
        check, events = self.links(missing={"2601.00001"})
        self.assertEqual(events, [("API", self.FIXTURE_IDS)])
        self.assertTrue(check.ok, check)
        self.assertEqual(check.observed, "5 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 1 manually confirmed; 0 dead; 0 not checked")
        check, events = self.links()
        self.assertEqual(check.observed, "5 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 0 manually confirmed; 0 dead; 0 not checked")

    def test_links_arxiv_batches(self):
        ids = [f"2602.{n:05d}" for n in range(1, 253)]
        self.write_links([f"https://arxiv.org/abs/{i}" for i in ids])
        check, events = self.links()
        self.assertTrue(check.ok, check)
        # 252 README ids plus the five fixture ids: batches of 100, 100 and 57, the scout's
        # ten seconds between them and none before the first.
        self.assertEqual([len(e[1]) if e[0] == "API" else e for e in events], [100, ("sleep", 10.0), 100, ("sleep", 10.0), 57])

    def test_links_arxiv_url_shapes_and_versions(self):
        self.write_links([
            "https://arxiv.org/abs/2602.00001", "https://arxiv.org/pdf/2602.00001v1",
            "https://www.arxiv.org/pdf/2602.00002v2.pdf", "https://arxiv.org/abs/2602.00002v1/",
            "https://arxiv.org/abs/2602.00003v1", "https://arxiv.org/abs/2602.00003v9",  # v9 does not exist, v1 does
            "https://arxiv.org/abs/cs/0101001v1", "https://arxiv.org/pdf/math.AG/0101002",  # legacy ids
            "https://arxiv.org/abs/2602.00004.pdf", "https://arxiv.org/abs/2602.00005?context=cs",  # not id URLs
            "https://arxiv.org/abs/2602.00006v0",  # versions start at 1, so this is not an id URL either
        ])
        check, events = self.links()
        self.assertEqual(events, [
            ("API", sorted(self.FIXTURE_IDS + ["2602.00001", "2602.00002", "2602.00003", "cs/0101001", "math.AG/0101002"])),
            # Shapes the id pattern rejects fall through to the paced page check; none is dropped.
            ("sleep", 10.0), ("HEAD", "https://arxiv.org/abs/2602.00004.pdf"),
            ("sleep", 10.0), ("HEAD", "https://arxiv.org/abs/2602.00005?context=cs"),
            ("sleep", 10.0), ("HEAD", "https://arxiv.org/abs/2602.00006v0"),
        ])
        self.assertEqual(check.details, ["https://arxiv.org/abs/2602.00003v9 -> version not listed by the arXiv export API (listed v2)"])
        self.assertEqual(check.observed, "16 unique URLs; 13 arXiv URLs as 10 ids via 1 API requests; 0 manually confirmed; 1 dead; 0 not checked")

    def test_links_arxiv_highest_listed_version_wins(self):
        self.write_links(["https://arxiv.org/abs/2602.00001v2", "https://arxiv.org/abs/2602.00001v4"])
        feed = "".join(f"<entry><id>http://arxiv.org/abs/{i}</id></entry>" for i in ["2602.00001v3", "2602.00001v1"] + [i + "v1" for i in self.FIXTURE_IDS])
        check, events = self.links(api_body=f'<feed xmlns="http://www.w3.org/2005/Atom">{feed}</feed>'.encode())
        self.assertEqual(check.details, ["https://arxiv.org/abs/2602.00001v4 -> version not listed by the arXiv export API (listed v3)"])

    def test_links_arxiv_api_failure_stops_all_arxiv_checks(self):
        self.write_links(["https://arxiv.org/html/2602.00001", "https://export.arxiv.org/abs/x?y", "https://example.org/a"])
        for status, label in ((429, "HTTP 429 (throttled), Retry-After 120"), (406, "HTTP 406 (throttled), Retry-After 120"), (500, "HTTP 500, Retry-After 120")):
            check, events = self.links(api_status={1: status}, retry_after="120")
            # One API request, no retry, no sleep on Retry-After, and no arXiv page request after the stop.
            self.assertEqual(events, [("API", self.FIXTURE_IDS), ("HEAD", "https://example.org/a")])
            self.assertEqual(check.observed, "8 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 0 manually confirmed; 0 dead; 7 not checked")
            self.assertEqual(check.details, [f"arXiv export API -> {label}: 7 URLs not checked." + self.STOP])
        for body, label in ((b"<html>busy</html>", "unexpected API response root html"), (b"not xml", "syntax error: line 1, column 0"),
                            (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#incorrect_id_format_for_x</id>'
                             b"<summary>incorrect id format for x</summary></entry></feed>", "API error entry: incorrect id format for x")):
            check, events = self.links(api_body=body)
            self.assertEqual(events, [("API", self.FIXTURE_IDS), ("HEAD", "https://example.org/a")])
            self.assertEqual(check.details, [f"arXiv export API -> {label}: 7 URLs not checked." + self.STOP])

    def test_links_arxiv_failure_in_a_later_batch(self):
        self.write_links([f"https://arxiv.org/abs/2602.{n:05d}" for n in range(1, 101)])
        check, events = self.links(api_status={2: 429}, missing={"2601.00001"})
        self.assertEqual([e[0] for e in events], ["API", "sleep", "API"])
        # The first batch's verdicts stand; only the second batch is unchecked.
        self.assertEqual(check.observed, "105 unique URLs; 105 arXiv URLs as 105 ids via 2 API requests; 0 manually confirmed; 1 dead; 5 not checked")
        self.assertEqual(check.details, [URLS[0] + " -> not listed by the arXiv export API",
                                         "arXiv export API -> HTTP 429 (throttled): 5 URLs not checked." + self.STOP])

    def test_links_page_checks_are_paced_and_stop_on_throttle(self):
        pages = ["https://arxiv.org/html/2602.00001", "https://arxiv.org/html/2602.00002", "https://arxiv.org/html/2602.00003",
                 "https://example.org/a", "https://example.org/b", "https://example.org/c"]
        self.write_links(pages)
        check, events = self.links(page_status={pages[1]: 406, pages[4]: 403}, retry_after="30")
        self.assertEqual(events, [
            ("API", self.FIXTURE_IDS),
            # html pages are not implied by the id, so they stay on the page check. arXiv hosts
            # share one pace with the API, and the 406 stops them: the third page is never asked.
            ("sleep", 10.0), ("HEAD", pages[0]), ("sleep", 10.0), ("HEAD", pages[1]),
            ("HEAD", pages[3]), ("sleep", 3.0), ("HEAD", pages[4]), ("sleep", 3.0), ("GET", pages[4]), ("sleep", 3.0), ("HEAD", pages[5]),
        ])
        self.assertEqual(check.observed, "11 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 0 manually confirmed; 1 dead; 2 not checked")
        self.assertEqual(check.details, [pages[4] + " -> HTTP 403",
                                         "arxiv.org -> HTTP 406 (throttled), Retry-After 30: 2 URLs not checked." + self.STOP])

    def test_links_throttle_on_get_fallback_and_confirmations_do_not_hide_a_stop(self):
        pages = ["https://example.org/a", "https://example.org/b"]
        self.write_links(pages)
        (self.root / "research/link-confirmations.txt").write_text("".join(f"2026-09-11 {url} -- Checked manually\n" for url in pages))
        check, events = self.links(page_status={("HEAD", pages[0]): 405, ("GET", pages[0]): 429}, retry_after="45")
        self.assertEqual(events[1:], [("HEAD", pages[0]), ("sleep", 3.0), ("GET", pages[0])])
        self.assertFalse(check.ok)
        self.assertEqual(check.observed, "7 unique URLs; 5 arXiv URLs as 5 ids via 1 API requests; 0 manually confirmed; 0 dead; 2 not checked")
        self.assertEqual(check.details, ["example.org -> HTTP 429 (throttled), Retry-After 45: 2 URLs not checked." + self.STOP])

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
