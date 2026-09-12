"""Scout command parity, constructive rendering and artifact failure boundaries."""

import argparse
from collections import OrderedDict
import contextlib
import datetime as dt
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from research_tools import arxiv_oai, records, scout
from research_tools.__main__ import main
from research_tools.profile import Profile, load_profile
from tests.test_arxiv_oai import DAY, FakeIO, SAMPLE, envelope, ok

FIXTURES = Path(__file__).parent / "fixtures"
# Captured from the old script before removal, fixed from/until 2026-09-08.
EXPECTED_REQUESTS = [
    "cs.AI: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3AAI&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "cs.CL: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3ACL&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "cs.LG: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3ALG&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "cs.SE: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3ASE&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "cs.CR: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3ACR&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "cs.HC: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=cs%3Acs%3AHC&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
    "stat.ML: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=stat%3Astat%3AML&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
]


def render_inputs():
    """Same inputs used to capture the legacy golden; matching fields are fixed values."""
    entries = [arxiv_oai.parse_record(element) for element in ET.fromstring(SAMPLE).findall(
        f"{arxiv_oai.OAI_NS}ListRecords/{arxiv_oai.OAI_NS}record")]
    entries[0].update(matched_anchors=["llm", "AI"], matched_topics=["evaluation"])
    entries[1].update(matched_anchors=["AI"], matched_topics=["prediction"])
    dedup = OrderedDict((r["id"], dict(r, appeared=["cs.AI"])) for r in entries)
    return dict(end_date=DAY, start_date=DAY, per_category=OrderedDict([("cs.AI", entries)]),
                deduped=dedup, new_ids=list(dedup), skipped_count=0, ledger=None,
                selected_categories=["cs.AI"], selected_groups=["fixture_topics"],
                anchors=["llm", "AI"], expand_on=OrderedDict())


class ScoutTests(unittest.TestCase):
    def setUp(self):
        guard = patch("http.client.HTTPSConnection", side_effect=AssertionError("live OAI access"))
        guard.start()
        self.addCleanup(guard.stop)
        guard = patch("time.sleep", side_effect=AssertionError("real sleep"))
        guard.start()
        self.addCleanup(guard.stop)

    def args(self, *flags):
        parser = argparse.ArgumentParser()
        scout.register(parser.add_subparsers())
        return parser.parse_args(["scout", "--start-date", "2026-09-08", "--end-date", "2026-09-08", *flags])

    def run_fake(self, fake, args, profile=None):
        if profile is None:
            profile = Profile(categories={"cs.AI": "AI"}, keyword_groups={"fixture": ["evaluation", "prediction"]})
        stdout, stderr = io.StringIO(), io.StringIO()
        client = fake.client()
        with patch.object(scout, "OAIClient", return_value=client) as factory, \
                patch.object(client, "close", wraps=client.close) as close, \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = scout.run(args, profile)
        factory.assert_called_once_with(delay_seconds=10.0, timeout=60.0)
        close.assert_called_with()
        self.assertGreaterEqual(close.call_count, 1)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_requests(self):
        profile = load_profile(scout.DEFAULT_CONFIG)
        self.assertEqual(scout.plan_requests(profile, DAY, DAY), EXPECTED_REQUESTS)
        self.assertEqual(scout.plan_requests(profile, DAY, DAY, "cs.SE", "executable_verification"),
                         [EXPECTED_REQUESTS[3]])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["scout", "--dry-run", "--start-date", "2026-09-08", "--end-date", "2026-09-08"]), 0)
        self.assertEqual(output.getvalue(), "\n".join(EXPECTED_REQUESTS) + "\n")

    def test_substitute_topic(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["scout", "--config", str(FIXTURES / "config-sample.json"),
                                   "--dry-run", "--start-date", "2026-09-08", "--end-date", "2026-09-08"]), 0)
        self.assertEqual(output.getvalue().splitlines(), [
            "q-bio.PE: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=q-bio%3Aq-bio%3APE&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
            "physics.ao-ph: https://oaipmh.arxiv.org/oai?verb=ListRecords&set=physics%3Aphysics%3Aao-ph&from=2026-09-08&until=2026-09-08&metadataPrefix=arXiv",
        ])

    def test_expand_on_merge_and_collision(self):
        profile = load_profile(FIXTURES / "config-sample.json")
        categories, groups, anchors, expand = scout.load_config(profile)
        self.assertEqual(list(groups), ["reef_health", "migration", "reef_temperature"])
        self.assertEqual(groups["reef_temperature"], ["thermal stress"])
        self.assertEqual(expand, {"reef_temperature": {"note": "notes/reef-temperature.md", "phrases": ["thermal stress"]}})
        self.assertEqual(anchors, ["coral", "plankton"])
        self.assertEqual(categories, profile.categories)
        self.assertNotIn("reef_temperature", profile.keyword_groups)
        with self.assertRaisesRegex(SystemExit, "expand_on slug collides with keyword group: same"):
            scout.load_config(Profile(keyword_groups={"same": ["a"]}, expand_on={"same": {"note": "n", "phrases": ["b"]}}))

    def test_golden_and_roundtrip(self):
        rendered = scout.render_markdown(**render_inputs())
        self.assertEqual(rendered.encode(), (FIXTURES / "scout-rendered-golden.md").read_bytes())
        doc = records.parse_scout(rendered)
        self.assertEqual([r.id for r in doc.deduped_candidates.entries], ["2609.01788", "2609.02746"])
        self.assertEqual(records.render_scout(doc), rendered)

    def test_capped_heading(self):
        args = render_inputs()
        rendered = scout.render_markdown(**args, capped_categories={"cs.AI"}, max_per_category=1)
        self.assertIn("### Category: `cs.AI` (set `cs:cs:AI`) (capped at --max-per-category 1; later matches in the window were not read)", rendered)
        self.assertEqual(records.parse_scout(rendered).category_results.categories[0].capped_at, 1)

    def test_outfile_ledger_and_suppression(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outfile, ledger = root / "nested/out.md", root / "seen.txt"
            ledger.write_text("2609.01788\n")
            code, stdout, stderr = self.run_fake(FakeIO([ok()]), self.args("--outfile", str(outfile), "--ledger", str(ledger)))
            self.assertEqual((code, stdout), (0, ""))
            self.assertEqual(stderr, f"harvesting cs.AI ...\nwrote {outfile}: 1 new candidates (1 suppressed by ledger)\n")
            doc = records.parse_scout(outfile.read_text())
            self.assertEqual([e.id for e in doc.deduped_candidates.entries], ["2609.02746"])
            self.assertIn(f"Ledger: {ledger} (1 already-seen candidates suppressed)", outfile.read_text())
            self.assertEqual(ledger.read_text(), "2609.01788\n2609.02746\n")
            # A second run suppresses both and does not append duplicates.
            code, _, stderr = self.run_fake(FakeIO([ok()]), self.args("--outfile", str(outfile), "--ledger", str(ledger)))
            self.assertEqual(code, 0)
            self.assertIn("0 new candidates (2 suppressed by ledger)", stderr)
            self.assertEqual(ledger.read_text(), "2609.01788\n2609.02746\n")
            self.assertEqual(records.parse_scout(outfile.read_text()).deduped_candidates.entries, ())

    def test_default_output_and_capped_run(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = FakeIO([ok(envelope(token="more"))])
            code, _, stderr = self.run_fake(fake, self.args("--outdir", directory, "--max-per-category", "1"))
            self.assertEqual(code, 0)
            output = Path(directory) / "scout-2026-09-08.md"
            self.assertEqual(records.parse_scout(output.read_text()).category_results.categories[0].capped_at, 1)
            self.assertIn("stopped at --max-per-category 1", stderr)
            self.assertEqual(len(fake.calls), 1)

    def test_raw_cap_no_artifact_or_ledger(self):
        """Removing the OAIError return before writes creates a partial artifact on raw-page cap."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, output = root / "ledger.txt", root / "out.md"
            ledger.write_text("retained\n")
            fake = FakeIO([ok(envelope(token="more"))] * 20)
            code, stdout, stderr = self.run_fake(fake, self.args("--outfile", str(output), "--ledger", str(ledger)))
            self.assertEqual((code, stdout), (1, ""))
            self.assertIn("OAI localPageLimit", stderr)
            self.assertFalse(output.exists())
            self.assertEqual(ledger.read_text(), "retained\n")
            self.assertEqual(len(fake.calls), 20)

    def test_http_failure_preserves_existing_output(self):
        """Removing the failed-harvest return overwrites old output or appends ledger IDs."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for response, message in [((429, "Limited", {}, b""), "rate limited by arXiv (HTTP 429)"),
                                      (ConnectionResetError("dropped"), "request failed")]:
                with self.subTest(response=response):
                    outfile, ledger = root / "out.md", root / "ledger.txt"
                    outfile.write_text("retained output")
                    ledger.write_text("retained ledger")
                    fake = FakeIO([response] * 3)
                    code, _, stderr = self.run_fake(fake, self.args("--outfile", str(outfile), "--ledger", str(ledger)))
                    self.assertEqual(code, 1)
                    self.assertIn(message, stderr)
                    self.assertEqual(outfile.read_text(), "retained output")
                    self.assertEqual(ledger.read_text(), "retained ledger")

    def test_invalid_arguments_and_fixed_spacing(self):
        for flags, message in [(("--days", "-1", "--start-date", "",), "--start-date must be on or before --end-date"),
                               (("--max-per-category", "0"), "--max-per-category must be positive"),
                               (("--retries", "-1"), "--retries must be non-negative"),
                               (("--retry-sleep", "0"), "--retry-sleep must be at least 1.0"),
                               (("--timeout", "1"), "--timeout must be at least 10.0"),
                               (("--categories", "unknown"), "unknown categories: unknown"),
                               (("--groups", "unknown"), "unknown groups: unknown")]:
            with self.subTest(flags=flags), self.assertRaises(SystemExit) as caught:
                scout.run(self.args("--dry-run", *flags), load_profile(scout.DEFAULT_CONFIG))
            self.assertEqual(str(caught.exception), message)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.args("--sleep", "10")
        self.assertEqual(caught.exception.code, 2)
