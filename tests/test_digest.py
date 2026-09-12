"""Digest byte parity, profile-driven behavior and command failures."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_tools import digest
from research_tools.profile import load_profile

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


class DigestTests(unittest.TestCase):
    def command(self, *extra, text=None, profile=None):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = FIXTURES / "triage-sample.md"
            if text is not None:
                source = directory / "input.md"
                source.write_text(text, encoding="utf-8")
            output = directory / "nested/digest.md"
            args = [sys.executable, "-m", "research_tools", "digest", "--input", str(source),
                    "--outfile", str(output), "--source-label", "fixture", *extra]
            if profile is not None:
                import json
                path = directory / "profile.json"
                path.write_text(json.dumps(profile), encoding="utf-8")
                args.extend(["--profile", str(path)])
            result = subprocess.run(args, cwd=ROOT, capture_output=True)
            return result, output.read_bytes() if output.exists() else None

    def test_golden_bytes_and_outfile(self):
        result, content = self.command("--decision", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(content, (FIXTURES / "digest-golden.md").read_bytes())
        self.assertIn(b"3 candidates shown; 3 matched filter", result.stdout)

    def test_padded_metadata_is_normalized(self):
        text = (FIXTURES / "triage-sample.md").read_text(encoding="utf-8")
        for before, after in (("Decision: promote\n", "Decision:  promote  \n"),
                              ("Initial label: operational technique\n", "Initial label: operational technique \n"),
                              ("Source: https://arxiv.org/abs/2605.30244\n", "Source: https://arxiv.org/abs/2605.30244 \n")):
            self.assertIn(before, text)
            text = text.replace(before, after, 1)
        tables = load_profile(ROOT / "research/scouts/config.json").digest_heuristics
        result, content = self.command("--decision", "promote", text=text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"Reinforcement Learning with Robust Rubric Rewards", content)
        self.assertIn(b"- Source: https://arxiv.org/abs/2605.30244\n", content)
        self.assertIn(b"- Suggested decision: promote\n", content)
        self.assertIn(b"- Suggested label: operational technique\n", content)
        self.assertIn(f"- Potential doc impact: {tables['doc_impact']['operational technique']}\n".encode(), content)
        self.assertNotIn(tables["doc_impact_fallback"].encode(), content.split(b"## 2.")[0])

    def test_substitute_tables_and_order(self):
        profile = load_profile(FIXTURES / "config-sample.json")
        candidate = replace(digest.parse_candidates(FIXTURES / "triage-sample.md")[0],
                            title="coral plankton", abstract="", key_claims=[], label="extends")
        tables = profile.digest_heuristics
        self.assertEqual(digest.evidence_type(candidate, tables), "reef survey")
        self.assertEqual(digest.topic_cluster(candidate, tables), "reef health")
        self.assertEqual(digest.read_priority(candidate, tables), 1)
        self.assertEqual(digest.doc_impact(candidate, tables), "may add habitat coverage")
        reordered = deepcopy(tables)
        reordered["evidence_types"].reverse()
        reordered["topic_clusters"].reverse()
        self.assertEqual(digest.evidence_type(candidate, reordered), "marine census")
        self.assertEqual(digest.topic_cluster(candidate, reordered), "ocean ecology")
        plankton = replace(candidate, title="plankton")
        self.assertEqual(digest.read_priority(plankton, tables), 2)
        reordered["read_priority"].reverse()
        self.assertEqual(digest.read_priority(plankton, reordered), 1)
        unknown = replace(candidate, title="unknown", label="unknown")
        self.assertEqual(digest.evidence_type(unknown, tables), "unknown marine evidence")
        self.assertEqual(digest.topic_cluster(unknown, tables), "other habitat")
        self.assertEqual(digest.read_priority(unknown, tables), 3)
        self.assertEqual(digest.doc_impact(unknown, tables), "unknown habitat impact")

    def test_substitute_profile_command(self):
        import json
        profile = json.loads((FIXTURES / "config-sample.json").read_text())
        text = (FIXTURES / "triage-sample.md").read_text().replace(
            "Reinforcement Learning with Robust Rubric Rewards", "coral plankton")
        result, content = self.command("--decision", "all", text=text, profile=profile)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"Evidence type: reef survey", content)
        self.assertIn(b"Topic cluster: reef health", content)

    def test_missing_tables(self):
        result, content = self.command(profile={"principles": {}, "canonical_docs": []})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, b"digest requires digest_heuristics in the profile\n")
        self.assertIsNone(content)

    def test_truncation_preserves_available_count(self):
        result, content = self.command("--decision", "all", "--max-items", "1")
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"Total candidates shown: 1\n", content)
        self.assertIn(b"Total candidates available after filter: 3\n", content)
        self.assertIn(b"1 candidates shown; 3 matched filter", result.stdout)
        self.assertNotIn(b"## 2.", content)

    def test_zero_max_rejected(self):
        result, content = self.command("--max-items", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"--max-items must be positive", result.stderr)
        self.assertIsNone(content)

    def test_ignore_filter(self):
        text = (FIXTURES / "triage-sample.md").read_text().replace(
            "Decision: promote", "Decision: ignore", 1)
        result, content = self.command("--decision", "ignore", text=text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"Total candidates shown: 1\n", content)
        self.assertIn(b"Suggested decision: ignore", content)
        self.assertNotIn(b"## 2.", content)

    def test_empty_filter_and_missing_input(self):
        result, content = self.command("--decision", "ignore")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"no candidates matched decision filter: ignore", result.stderr)
        self.assertIsNone(content)
        result, content = self.command("--input", "/nonexistent/research-tools-digest.md")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"input not found:", result.stderr)
        self.assertIsNone(content)

    def test_parse_error_has_file_and_line(self):
        result, content = self.command(text="invalid note\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"input.md: line 1:", result.stderr)
        self.assertIsNone(content)

    def test_optional_sections_and_prose_helpers(self):
        text = (FIXTURES / "triage-sample.md").read_text().replace(
            "### Decision", "### Needs Human Review\n\n- Check sampling.\n\n"
            "### Credibility Flags\n\n- Narrow sample.\n- Preliminary.\n\n### Decision", 1)
        result, content = self.command("--decision", "all", text=text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"Human question: Check sampling.", content)
        self.assertIn(b"Credibility flags: Narrow sample.; Preliminary.", content)
        self.assertEqual(digest.one_line(" a" + chr(0x2014) + "b\n c "), "a; b c")
        self.assertEqual(digest.first_sentence("First. Second."), "First.")
        self.assertEqual(digest.first_sentence(""), "(none)")
        self.assertEqual(digest.first_sentence("abcdefghijk", 8), "abcde...")
