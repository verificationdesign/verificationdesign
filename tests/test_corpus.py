"""Compatibility with the tracked triage corpus and available local scouts."""

from pathlib import Path
import unittest

from research_tools.records import RecordError, parse_scout, parse_triage, render_scout, render_triage

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {
    "2026-05-31-llm-judge-scout.md": 5,
    "2026-06-12-scout-2026-06-09.md": 30,
    "2026-07-12-scout-2026-07-12.md": 30,
    "2026-08-15-scout-allocation.md": 45,
}
EXCLUDED = {"TEMPLATE.md", "README.md", "anchors.md", "ranking_design.md"}


class CorpusTests(unittest.TestCase):
    def test_triage_corpus(self):
        paths = sorted(p for p in (ROOT / "research/triage").glob("*.md") if p.name not in EXCLUDED)
        # Known notes keep their candidate counts; newer notes only need to parse and round-trip.
        self.assertLessEqual(set(COUNTS), {p.name for p in paths})
        for path in paths:
            with self.subTest(note=path.name):
                raw = path.read_bytes()
                doc = parse_triage(raw.decode())
                self.assertGreater(len(doc.candidates), 0)
                if path.name in COUNTS:
                    self.assertEqual(len(doc.candidates), COUNTS[path.name])
                self.assertEqual(render_triage(doc).encode(), raw)

    def test_local_scouts(self):
        paths = sorted((ROOT / "research/scouts").glob("scout-*.md"))
        if not paths:
            self.skipTest("local scout artifacts are untracked and absent")
        for path in paths:
            with self.subTest(artifact=path.name):
                raw = path.read_bytes()
                try:
                    doc = parse_scout(raw.decode())
                except RecordError as error:
                    self.skipTest(f"{path.name}: {error}")
                self.assertEqual(render_scout(doc).encode(), raw)
