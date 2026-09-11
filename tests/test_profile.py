"""Topic profile validation, ordering and a substitute subject."""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import tempfile
import unittest

from research_tools.profile import load_profile

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tests/fixtures/config-sample.json"


class ProfileTests(unittest.TestCase):
    def test_real_profile(self):
        profile = load_profile(ROOT / "research/scouts/config.json")
        self.assertEqual(len(profile.categories), 7)
        self.assertEqual(len(profile.keyword_groups), 13)
        self.assertEqual(len(profile.anchor_phrases), 5)
        self.assertEqual(len(profile.expand_on), 3)
        self.assertEqual(list(profile.principles), [f"principle-{n}" for n in range(1, 10)])
        headings = [line.split(". ", 1)[1] for line in
                    (ROOT / "verification_design.md").read_text().splitlines()
                    if line.startswith("### ") and line[4:5].isdigit()]
        self.assertEqual(list(profile.principles.values()), headings)
        self.assertEqual(profile.canonical_docs, ["verification_design.md"])

    def test_substitute_topic_and_order(self):
        profile = load_profile(SAMPLE)
        self.assertEqual(list(profile.categories), ["q-bio.PE", "physics.ao-ph"])
        self.assertEqual(list(profile.keyword_groups), ["reef_health", "migration"])
        self.assertEqual(profile.keyword_groups["reef_health"], ["coral bleaching", "reef recovery"])
        self.assertEqual(profile.anchor_phrases, ["coral", "plankton"])
        self.assertEqual(profile.expand_on, {"reef_temperature": {
            "note": "notes/reef-temperature.md", "phrases": ["thermal stress"]}})
        self.assertEqual(list(profile.principles), ["reef-2", "reef-1"])
        self.assertEqual(profile.canonical_docs, ["marine-notes.md"])
        with self.assertRaises(FrozenInstanceError):
            profile.categories = {}

    def test_invalid_profiles(self):
        cases = [
            ({"extra": 1}, (), "unknown profile key: extra"),
            ({}, ("principles",), "missing profile key: principles"),
            ({}, ("canonical_docs",), "missing profile key: canonical_docs"),
            ({"expand_on": {"reef_health": {"note": "x", "phrases": []}}}, (), "collides.*reef_health"),
            ({"categories": []}, (), "categories must be an object"),
            ({"keyword_groups": {"reef": "coral"}}, (), "invalid keyword_groups entry: reef"),
            ({"expand_on": {"reef": {"note": 5, "phrases": []}}}, (), "invalid expand_on entry: reef"),
            ({"principles": {"reef": 1}}, (), "invalid principles entry: reef"),
            ({"canonical_docs": "marine.md"}, (), "canonical_docs must be a list"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            for changes, removed, message in cases:
                with self.subTest(message=message):
                    data = json.loads(SAMPLE.read_text())
                    data.update(changes)
                    for key in removed:
                        del data[key]
                    path.write_text(json.dumps(data))
                    with self.assertRaisesRegex(ValueError, message):
                        load_profile(path)

    def test_optional_fields_default_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text('{"principles": {}, "canonical_docs": []}')
            profile = load_profile(path)
            self.assertEqual(profile.categories, {})
            self.assertEqual(profile.keyword_groups, {})
            self.assertEqual(profile.anchor_phrases, [])
            self.assertEqual(profile.expand_on, {})
