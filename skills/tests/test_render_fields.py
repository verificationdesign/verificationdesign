"""Inventory HF: exact shared header and source formatting."""
import json
from pathlib import Path
import tempfile
from support import ROOT, ScriptCase, fixture, module


class RenderFieldsTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.fields = module("render_fields")
        self.catalog, self.meta = module("load_catalog").load_catalog()
        self.data = fixture()

    def header(self):
        return self.fields.header("Findings", self.data, self.catalog, self.meta)

    def test_hf_1_document_header(self):
        self.assertEqual(self.header()[:10], ["# Findings", "", "Artifact: " + self.data["artifact"], "",
             "Scope: " + self.data["scope"], "", "Corpus revision: `" + self.catalog["revision"] + "`", "",
             "Corpus tag: `" + self.meta["corpus-tag"] + "`", ""])

    def test_hf_2_skill_pins_and_models(self):
        self.data["models"] = {"generator": "Family G", "verifier": "Family V"}
        head = self.header()
        skill = self.data["skill"]
        self.assertIn(f'Skill: {skill["name"]} {skill["version"]}', head)
        pins = "; ".join(f'{k[:-7]} `{v}`' for k, v in skill.items() if k.endswith("_sha256"))
        self.assertIn("Skill pins: " + pins, head)
        self.assertIn("Generator model: Family G", head)
        self.assertIn("Verifier model: Family V", head)

    def test_hf_3_artifact_identity(self):
        for revision, label in (("fixture-revision", "fixture-revision"), (None, "not recorded")):
            self.data["artifact_identity"] = {"revision": revision, "files": [{"path": "check.py", "sha256": "a" * 64}]}
            head = self.header()
            line = f"Artifact identity: revision {label}; 1 files"
            self.assertIn(line, head)
            self.assertIn("- check.py: `" + "a" * 64 + "`", head)
            self.assertLess(head.index(line), head.index("## Assumptions"))
        del self.data["artifact_identity"]
        self.assertFalse(any(line.startswith("Artifact identity:") for line in self.header()))

    def test_hf_4_assumption_bullets_and_empty(self):
        self.data.pop("measurements", None)
        self.data["assumptions"] = [{"topic": "first", "statement": "One."}, {"topic": "second", "statement": "Two."}]
        self.assertEqual(self.header()[self.header().index("## Assumptions"):],
                         ["## Assumptions", "", "- first: One.", "- second: Two.", ""])
        self.data["assumptions"] = []
        self.assertEqual(self.header()[-4:], ["## Assumptions", "", "None.", ""])

    def test_hf_5_measurement_metadata_and_command(self):
        self.data["measurements"] = [dict(id="probe", kind="execution", env={"Z": "last", "A": "first"},
            exit_code=7, artifact_revision="rev42", log="probe.log", note="Observed only.", command="first\nsecond")]
        head = self.header()
        expected = ['- probe: kind execution; env `{"A": "first", "Z": "last"}`; exit 7; artifact revision `rev42`; log probe.log; note: Observed only.',
                    "", "```text", "first\nsecond", "```", ""]
        self.assertEqual(head[head.index("## Measurements"):], ["## Measurements", ""] + expected)
        self.data["measurements"][0]["log"] = None
        self.assertIn(expected[0].replace("log probe.log", "log none"), self.header())
        self.data["measurements"] = []
        self.assertEqual(self.header()[-4:], ["## Measurements", "", "None.", ""])
        del self.data["measurements"]
        self.assertNotIn("## Measurements", self.header())

    def test_hf_6_unavailable_json(self):
        rows = [dict(unavailable=True, source_url="https://example.invalid/one", reason="offline"),
                dict(unavailable=True, source_url="https://example.invalid/two", reason="unavailable")]
        self.assertEqual(self.fields.unavailable({"unavailable_sources": rows}),
                         ["### Unavailable sources", ""] +
                         [line for row in rows for line in ("```json", json.dumps(row, indent=2, ensure_ascii=False), "```", "")])
        self.assertEqual(self.fields.unavailable({}), [])
        self.assertEqual(self.fields.unavailable({"unavailable_sources": []}), [])

    def test_hf_7_source_pairs_and_unique_definitions(self):
        sources = self.fields.Sources()
        cards = self.catalog["cards"][:2]
        for card in cards + cards:
            slug = card["id"].split("/")[-1]
            self.assertEqual(sources.card(card), f'[{card["title"]}][{slug}] ([pinned source][{slug}-src])')
        principles = self.catalog["principles"]
        expected = ["## Sources", "", f'Corpus revision: `{self.catalog["revision"]}`.', "",
                    "Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).", "",
                    f'[principles]: {principles["html_url"]}', f'[principles-src]: {principles["source_url"]}']
        for card in cards:
            slug = card["id"].split("/")[-1]
            expected += [f'[{slug}]: {card["html_url"]}', f'[{slug}-src]: {card["source_url"]}']
        self.assertEqual(sources.render(self.catalog["revision"], principles), expected + [""])
        self.assertEqual(self.fields.Sources().render(self.catalog["revision"], principles), expected[:8] + [""])

    def test_hf_3_optional_fields_in_both_renderers(self):
        for kind, folder, validator, renderer in (
            ("design", "design-sound", "validate_judgments.py", "render_plan.py"),
            ("audit", "audit-known-defect", "validate_findings.py", "render_findings.py")):
            record = json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())
            record["artifact_identity"] = {"revision": "fixture-revision", "files": [{"path": "check.py", "sha256": "a" * 64}]}
            record["measurements"] = [{"id": "probe", "kind": "execution", "command": "python3 check.py", "env": {"MODE": "test"}, "exit_code": 0, "artifact_revision": "fixture-revision", "log": "probe.log", "note": "Observed only."}]
            record["unavailable_sources"] = [{"unavailable": True, "source_url": "https://example.invalid/source", "reason": "offline"}]
            with tempfile.TemporaryDirectory() as tmp:
                path, output = Path(tmp) / "record.json", Path(tmp) / "output.md"
                for present in (True, False):
                    if not present:
                        for key in ("artifact_identity", "measurements", "unavailable_sources", "priority"):
                            record.pop(key, None)
                    path.write_text(json.dumps(record))
                    result = self.run_script(kind, validator, path)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    if kind == "audit":
                        routed = self.run_script(kind, "route_failures.py", path)
                        path.write_text(routed.stdout)
                    result = self.run_script(kind, renderer, path, "--output", output)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    text = output.read_text()
                    self.assertEqual("Artifact identity:" in text, present)
                    self.assertEqual("## Measurements" in text, present)
                    self.assertEqual('"unavailable": true' in text, present)
                    self.assertEqual("### Unavailable sources" in text, present)
                    if present:
                        self.assertLess(text.index("### Unavailable sources"), text.index('"unavailable": true'))
                        self.assertLess(text.index('"unavailable": true'), text.index("## Sources"))
                    if present:
                        self.assertLess(text.index("Artifact identity:"), text.index("## Assumptions"))
                        self.assertLess(text.index("## Assumptions"), text.index("## Measurements"))
                        self.assertLess(text.index("## Measurements"), text.index("## Summary"))
                        self.assertIn("- probe:", text)
                        self.assertIn("Artifact identity: revision fixture-revision; 1 files\n", text)
                        self.assertIn("- check.py: `" + "a" * 64 + "`\n", text)
                    if kind == "design":
                        self.assertIn("Instantiation:", text)
