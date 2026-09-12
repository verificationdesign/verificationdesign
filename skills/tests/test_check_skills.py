"""Mechanical parser, judgment rule, and record boundary checks."""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_skills", ROOT / "skills/check_skills.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
DESIGN = ROOT / "skills/verification-design"
sys.path.insert(0, str(DESIGN / "scripts"))
from validate_judgments import decision, validate


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.text = (DESIGN / "SKILL.md").read_text()
        self.yaml = (DESIGN / "agents/openai.yaml").read_text()

    def test_good_frontmatter_and_host_policy(self):
        self.assertEqual(checker.frontmatter_errors(self.text, DESIGN.name, self.yaml), [])
        parsed = checker.parse_frontmatter(self.text)
        self.assertIs(parsed["disable-model-invocation"], True)
        self.assertEqual(parsed["metadata"]["disable-model-invocation"], "true")

    def test_bad_description(self):
        for phrase in ("use when", "whenever", "automatically", "trigger"):
            with self.subTest(phrase=phrase):
                bad = self.text.replace("Write a verification plan", phrase + " a verification plan")
                self.assertTrue(checker.frontmatter_errors(bad, DESIGN.name, self.yaml))

    def test_missing_explicit_request_sentence(self):
        self.assertTrue(checker.frontmatter_errors(self.text.replace("Do not run without an explicit request.", ""), DESIGN.name, self.yaml))

    def test_wrong_name_and_flag_types(self):
        for old, new in (("name: verification-design", "name: Wrong_Name"), ("disable-model-invocation: true\n", 'disable-model-invocation: "true"\n'), ('  disable-model-invocation: "true"', "  disable-model-invocation: true")):
            with self.subTest(new=new):
                self.assertTrue(checker.frontmatter_errors(self.text.replace(old, new, 1), DESIGN.name, self.yaml))

    def test_bad_yaml_policy(self):
        for value in ("true", '"false"'):
            self.assertTrue(checker.frontmatter_errors(self.text, DESIGN.name, self.yaml.replace("false", value)))

    def test_frontmatter_missing_or_unclosed(self):
        for text in ("name: example\n", "---\nname: example\n"):
            with self.assertRaises(ValueError):
                checker.parse_frontmatter(text)

    def test_yaml_subset_good(self):
        self.assertEqual(checker.parse_yaml_subset('policy:\n  enabled: false\n  text: "true"\nname: example\n'), {"policy": {"enabled": False, "text": "true"}, "name": "example"})

    def test_yaml_subset_rejects_ambiguous_inputs(self):
        for text in ('a: x\na: y\n', '  a: x\n', 'a:\n    b: true\n', 'a: "unterminated\n', 'a: [x]\n', 'a:\n  b:\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.parse_yaml_subset(text)

    def test_normalization_crlf(self):
        self.assertEqual(checker.normalize_body(b"one\r\ntwo\r\n\r\n"), b"one\ntwo\n")
        self.assertEqual(checker.normalize_body(b"one\n"), b"one\n")
        self.assertEqual(checker.normalize_body(b""), b"\n")


class DecisionTests(unittest.TestCase):
    def test_all_nine_decision_combinations(self):
        expected = {
            ("holds", "holds"): "reject", ("holds", "does-not-hold"): "apply", ("holds", "unknown"): "undecided",
            ("does-not-hold", "holds"): "reject", ("does-not-hold", "does-not-hold"): "reject", ("does-not-hold", "unknown"): "reject",
            ("unknown", "holds"): "reject", ("unknown", "does-not-hold"): "undecided", ("unknown", "unknown"): "undecided",
        }
        for pair in itertools.product(("holds", "does-not-hold", "unknown"), repeat=2):
            with self.subTest(pair=pair):
                self.assertEqual(decision([pair[0]], [pair[1]]), expected[pair])

    def test_malformed_records_fail_validation_without_crash(self):
        catalog, _ = checker.loader.load_catalog()
        for value in (None, [], {}, {"cards": [None]}, {"cards": [{}]}):
            with self.subTest(value=value):
                self.assertTrue(validate(value, catalog))

    def test_duplicate_card_rejected(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        record["cards"].append(copy.deepcopy(record["cards"][0]))
        self.assertIn("coverage", {error["rule"] for error in validate(record)})

    def test_unknown_exclusion_cannot_apply(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        card = next(c for c in record["cards"] if c["decision"] == "apply")
        card["do_not_use_when"][0]["verdict"] = "unknown"
        self.assertIn("decision-undecided", {error["rule"] for error in validate(record)})


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())

    def assert_plan_error(self):
        self.assertEqual({error["rule"] for error in validate(self.record)}, {"plan"})

    def test_missing_or_non_object_plan(self):
        self.record.pop("plan")
        self.assert_plan_error()
        for value in (None, [], "design"):
            self.record["plan"] = value
            self.assert_plan_error()

    def test_plan_keys(self):
        original = copy.deepcopy(self.record["plan"])
        for key in ("design", "requirements"):
            self.record["plan"] = copy.deepcopy(original)
            self.record["plan"].pop(key)
            self.assert_plan_error()
        self.record["plan"] = dict(original, extra=True)
        self.assert_plan_error()

    def test_plan_design_nonempty_string(self):
        for value in (None, [], 1, "", " "):
            self.record["plan"]["design"] = value
            self.assert_plan_error()

    def test_plan_source_nonempty_string_when_present(self):
        for value in (None, [], 1, "", " "):
            self.record["plan"]["source"] = value
            self.assert_plan_error()
        self.record["plan"].pop("source")
        self.assertEqual(validate(self.record), [])

    def test_requirements_nonempty_list(self):
        for value in (None, {}, "V1", []):
            self.record["plan"]["requirements"] = value
            self.assert_plan_error()

    def test_requirement_object_and_exact_keys(self):
        original = copy.deepcopy(self.record["plan"]["requirements"][0])
        variants = [None, [], {}, dict(original, extra=True)]
        variants += [{k: v for k, v in original.items() if k != key} for key in original]
        for value in variants:
            self.record["plan"]["requirements"][0] = value
            self.assert_plan_error()

    def test_requirement_ids_contiguous_in_order(self):
        for value in ("V3", "V1", "v2", 2, None, []):
            self.record["plan"]["requirements"][1]["id"] = value
            self.assert_plan_error()
        self.record["plan"]["requirements"][1]["id"] = "V2"
        self.record["plan"]["requirements"].reverse()
        self.assert_plan_error()

    def test_requirement_statement_nonempty_string(self):
        for value in (None, [], 1, "", " "):
            self.record["plan"]["requirements"][0]["statement"] = value
            self.assert_plan_error()

    def test_requirement_check_nonempty_string(self):
        for value in (None, [], 1, "", " "):
            self.record["plan"]["requirements"][0]["check"] = value
            self.assert_plan_error()

    def test_patterns_must_be_list(self):
        for value in (None, {}, "verification/comparator"):
            self.record["plan"]["requirements"][1]["patterns"] = value
            self.assert_plan_error()

    def test_patterns_name_only_applied_cards(self):
        for value in (None, [], {}, "missing/card", "context-and-state/constitution"):
            self.record["plan"]["requirements"][1]["patterns"] = [value]
            self.assert_plan_error()
        self.record = json.loads((ROOT / "skills/fixtures/design-resolved/record.json").read_text())
        self.record["plan"]["requirements"][1]["patterns"] = ["verification/executable-analog"]
        self.assert_plan_error()

    def test_patterns_no_duplicates_within_requirement(self):
        patterns = self.record["plan"]["requirements"][0]["patterns"]
        patterns.append(patterns[0])
        self.assert_plan_error()

    def test_every_applied_card_serves_requirement(self):
        self.record["plan"]["requirements"][0]["patterns"].pop()
        self.assert_plan_error()

    def test_empty_patterns_and_card_serving_multiple_requirements(self):
        self.assertEqual(validate(self.record), [])
        self.record["plan"]["requirements"][1]["patterns"] = ["verification/comparator"]
        self.assertEqual(validate(self.record), [])

    def test_plan_render_order_sources_and_served_requirements(self):
        from render_plan import render
        from load_catalog import load_catalog
        catalog, meta = load_catalog()
        self.record["plan"]["requirements"][1]["patterns"] = ["verification/comparator"]
        before = copy.deepcopy(self.record)
        text = render(self.record, catalog, meta)
        self.assertEqual(self.record, before)
        self.assertEqual([line for line in text.splitlines() if line.startswith("## ")], [
            "## Design", "## Verification requirements", "## Assumptions", "## Measurements",
            "## Summary", "## Workflow characterization", "## Patterns applied",
            "## Patterns rejected", "## Not verified", "## Sources"])
        self.assertIn("Source: artifact/workflow.md", text)
        self.assertIn("Requirements: 2", text)
        applied = text.split("## Patterns applied", 1)[1].split("## Patterns rejected", 1)[0]
        self.assertIn("Decision: apply\n\nServes: V1, V2", applied)
        requirements = text.split("## Verification requirements", 1)[1].split("## Assumptions", 1)[0]
        self.assertLess(requirements.index("[Comparator][comparator]"), requirements.index("[Executable Analog][executable-analog]"))
        self.assertEqual(text.count("[comparator]: "), 1)
        self.assertEqual(text, render(self.record, catalog, meta))
        self.record["plan"].pop("source")
        self.record.pop("measurements")
        self.record["plan"]["requirements"][1]["patterns"] = []
        text = render(self.record, catalog, meta)
        self.assertNotIn("Source: artifact/workflow.md", text)
        self.assertNotIn("## Measurements", text)
        self.assertIn("Patterns: none", text)


class OutputBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.record = Path(self.tmp.name) / "record.json"
        self.output = Path(self.tmp.name) / "output.md"

    def call(self, skill, script, record, output=False):
        self.record.write_text(json.dumps(record))
        command = [sys.executable, str(ROOT / "skills" / skill / "scripts" / script), str(self.record)]
        if output:
            command += ["--output", str(self.output)]
        return subprocess.run(command, capture_output=True, text=True)

    def test_invalid_design_record_cannot_write_plan(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        record["cards"].pop()
        result = self.call("verification-design", "render_plan.py", record, output=True)
        self.assertEqual(result.returncode, 3)
        self.assertFalse(self.output.exists())

    def test_unknown_on_rejected_card_surfaces_in_plan(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        card = next(c for c in record["cards"] if c["decision"] == "reject")
        card["do_not_use_when"][0]["verdict"] = "unknown"
        card["do_not_use_when"][0]["evidence"] = "The artifact does not establish this exclusion."
        result = self.call("verification-design", "render_plan.py", record, output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(card["do_not_use_when"][0]["condition"], self.output.read_text().split("## Not verified", 1)[1])

    def test_audit_missing_question_fails_coverage(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        record["checks"].pop(0)
        result = self.call("verification-audit", "validate_findings.py", record)
        self.assertEqual(result.returncode, 3)
        self.assertIn("coverage", {e["rule"] for e in json.loads(result.stdout)})

    def test_unmapped_free_defect_routes_to_no_card(self):
        record = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        record["checks"].append({"free": True, "principle": 5, "question": "Does the report preserve the criterion identifier?", "status": "defect", "evidence": "Illustrative report row omits its criterion identifier.", "failure": "unmapped", "failure_note": "Missing criterion identifier in the emitted row.", "severity": "low"})
        routed = self.call("verification-audit", "route_failures.py", record)
        self.assertEqual(routed.returncode, 0, routed.stdout + routed.stderr)
        routed_record = json.loads(routed.stdout)
        self.assertEqual(routed_record["checks"][-1]["cards"], [])
        self.assertIs(routed_record["checks"][-1]["routed"], False)
        rendered = self.call("verification-audit", "render_findings.py", routed_record, output=True)
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("No routed card: outside the six mapped failures; see the failure note above.", text)
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["## Assumptions", "## Summary", "## Defects", "## Checked and sound", "## Not applicable", "## Not checked", "## Insufficient evidence", "## Observed outside scope", "## Sources"])

    def test_related_cards_rendered_as_judged_and_candidates(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        defect = next(c for c in record["checks"] if c["status"] == "defect")
        self.assertEqual(defect["related_cards"], ["verification/blind-oracle"])
        rendered = self.call("verification-audit", "render_findings.py", record, output=True)
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("Candidate cards from the failure map (a lookup, not an applicability judgment):", text)
        self.assertIn("- judged applicable: [Blind Oracle]", text)
        self.assertIn("- candidate: [Cross-Family]", text)
        self.assertIn("Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).", text)
        defect["related_cards"] = ["verification/comparator"]
        result = self.call("verification-audit", "validate_findings.py", record)
        self.assertEqual(result.returncode, 3)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"routing"})
        non_defect = next(c for c in record["checks"] if c["status"] == "not-checked")
        defect["related_cards"] = ["verification/blind-oracle"]
        non_defect["related_cards"] = ["verification/blind-oracle"]
        result = self.call("verification-audit", "validate_findings.py", record)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"routing"})

    def test_non_string_failure_with_related_cards_reports_failure(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        defect = next(c for c in record["checks"] if c["status"] == "defect")
        defect["failure"] = []
        defect["related_cards"] = ["verification/blind-oracle"]
        result = self.call("verification-audit", "validate_findings.py", record)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("failure", {e["rule"] for e in json.loads(result.stdout)})

    def test_unmapped_defect_with_related_cards_names_them(self):
        record = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        record["checks"].append({"free": True, "principle": 5, "question": "Does the report preserve the criterion identifier?", "status": "defect", "evidence": "Illustrative report row omits its criterion identifier.", "failure": "unmapped", "failure_note": "Missing criterion identifier in the emitted row.", "severity": "low", "related_cards": ["context-and-state/constitution"]})
        rendered = self.call("verification-audit", "render_findings.py", record, output=True)
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("Cards named by judgment (the failure map has no entry for this defect):", text)
        self.assertIn("- judged applicable: [Constitution]", text)

    def test_requirement_references_checked_against_plan(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        card = next(c for c in record["cards"] if c["decision"] == "apply")
        card["use_when"][0]["evidence"] += " Serves V1 and V9."
        self.record.write_text(json.dumps(record))
        result = subprocess.run([sys.executable, str(ROOT / "skills/verification-design/scripts/check_citations.py"), str(self.record), "--root", str(ROOT / "skills/fixtures/design-sound")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["counts"]["unknown-requirement"], 1)
        self.assertGreaterEqual(data["counts"]["requirements"], 1)
        self.assertIn({"citation": "V9", "entry": "$.cards[%d].use_when[0].evidence" % record["cards"].index(card), "status": "unknown-requirement"}, data["citations"])

    def test_requirement_statement_references_checked_against_plan(self):
        record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
        record["plan"]["requirements"][0]["statement"] += " Depends on V9."
        self.record.write_text(json.dumps(record))
        result = subprocess.run([sys.executable, str(ROOT / "skills/verification-design/scripts/check_citations.py"), str(self.record), "--root", str(ROOT / "skills/fixtures/design-sound")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["counts"]["unknown-requirement"], 1)
        self.assertIn({"citation": "V9", "entry": "$.plan.requirements[0].statement", "status": "unknown-requirement"}, data["citations"])

    def test_scripts_create_output_directory(self):
        target = Path(self.tmp.name) / "dated" / "run" / "record.json"
        result = subprocess.run([sys.executable, str(ROOT / "skills/verification-audit/scripts/scaffold_record.py"), "--artifact", "a", "--scope", "s", "--output", str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(target.exists())

    def test_tampered_routing_cannot_write_findings(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        routed = self.call("verification-audit", "route_failures.py", record)
        self.assertEqual(routed.returncode, 0)
        record = json.loads(routed.stdout)
        defect = next(c for c in record["checks"] if c["status"] == "defect")
        defect["cards"][0]["source_url"] = "https://example.invalid/mutable"
        result = self.call("verification-audit", "render_findings.py", record, output=True)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)[0]["rule"], "routing")
        self.assertFalse(self.output.exists())


class ReleaseTests(unittest.TestCase):
    def run_script(self, kind, name, *args):
        return checker.run([sys.executable, str(ROOT / "skills" / ("verification-" + kind) / "scripts" / name), *map(str, args)])

    def test_python_guard(self):
        from unittest.mock import patch
        import io
        from contextlib import redirect_stderr
        from load_catalog import require_python
        with patch.object(sys, "version_info", (3, 9, 6)), redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as exc:
                require_python()
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(stderr.getvalue(), "Python 3.9.6 found; Python 3.11 or later required\n")
        with patch.object(sys, "version_info", (3, 11, 0)):
            require_python()

    def test_scaffolds_copy_fields_and_fail_validation(self):
        catalog = json.loads((DESIGN / "assets/catalog.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            for kind, counts, rules in (("design", {"cards": 17, "conditions": 156}, {"assumptions", "structure", "models", "plan"}),
                                        ("audit", {"checks": 18}, {"status", "evidence", "models"})):
                path = Path(tmp) / (kind + ".json")
                result = self.run_script(kind, "scaffold_record.py", "--artifact", "test artifact", "--scope", "test scope", "--output", path)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["counts"], counts)
                record = json.loads(path.read_text())
                self.assertEqual(record["corpus_revision"], catalog["revision"])
                self.assertEqual(record["models"], {"generator": "", "verifier": ""})
                self.assertEqual(record["skill"]["name"], "verification-" + kind)
                self.assertEqual(record["skill"]["version"], checker.parse_frontmatter((DESIGN / "SKILL.md").read_text())["metadata"]["version"])
                self.assertEqual("checklist_sha256" in record["skill"], kind == "audit")
                if kind == "design":
                    self.assertEqual([c["id"] for c in record["cards"]], [c["id"] for c in catalog["cards"]])
                    self.assertTrue(all("resolution" not in c for c in record["cards"]))
                    self.assertEqual(record["plan"], {"design": "", "requirements": []})
                    for card, source in zip(record["cards"], catalog["cards"]):
                        for group in ("use_when", "do_not_use_when"):
                            self.assertEqual([c["condition"] for c in card[group]], source[group])
                            self.assertTrue(all(c["verdict"] == c["evidence"] == "" for c in card[group]))
                else:
                    lines = (ROOT / "skills/verification-audit/references/principles-checklist.md").read_text().splitlines()
                    self.assertEqual([c["question"] for c in record["checks"]], [line[2:] for line in lines if line.startswith("- ")])
                result = self.run_script(kind, "validate_judgments.py" if kind == "design" else "validate_findings.py", path)
                self.assertEqual(result.returncode, 3)
                self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, rules)
                envelope = self.run_script(kind, "scaffold_record.py", "--artifact", "test artifact", "--scope", "test scope", "--output", "-")
                self.assertEqual(json.loads(envelope.stdout), {"record": record, "counts": counts})

    def test_citation_existence_bounds_and_selected_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.txt").write_text("one\ntwo\nthree")
            record = {"evidence": "sample.txt:1 sample.txt:2-3 sample.txt:4 missing.txt:1 sample.txt:1",
                      "assumptions": [{"statement": str(root / "sample.txt") + ":3"}],
                      "measurements": [{"note": "sample.txt:0 sample.txt:3-2"}],
                      "reason": "sample.txt:1", "instantiation": "missing/thing:2",
                      "question": "ignore.txt:1", "command": "ignore.txt:2"}
            path = root / "record.json"; path.write_text(json.dumps(record))
            for kind in ("design", "audit"):
                result = self.run_script(kind, "check_citations.py", path, "--root", root)
                self.assertEqual(result.returncode, 3, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["counts"], {"found": 3, "missing": 2, "out-of-bounds": 3, "requirements": 0, "unknown-requirement": 0})
                self.assertEqual(len(report["citations"]), 5)
                self.assertTrue(all(x["entry"].startswith("$.") for x in report["citations"]))
                path.write_text(json.dumps({"evidence": "sample.txt:1-3"}))
                good = self.run_script(kind, "check_citations.py", path, "--root", root)
                self.assertEqual(good.returncode, 0)
                self.assertEqual(json.loads(good.stdout)["counts"], {"found": 1, "missing": 0, "out-of-bounds": 0, "requirements": 0, "unknown-requirement": 0})
                path.write_text(json.dumps(record))

    def test_resolution_positive_and_four_negative_fixtures(self):
        folder = ROOT / "skills/fixtures/design-resolved"
        record = json.loads((folder / "record.json").read_text())
        self.assertEqual(validate(record), [])
        for name in ("applied", "bad-date", "unknown-measurement", "extra-key"):
            with self.subTest(name=name):
                path = folder / f"negative-resolution-{name}.json"
                result = self.run_script("design", "validate_judgments.py", path)
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"resolution"})

    def test_resolution_types_calendar_dates_and_absent_measurements(self):
        original = json.loads((ROOT / "skills/fixtures/design-resolved/record.json").read_text())
        for field, value in (("date", None), ("date", "20260910"), ("date", "2026-W37-4"),
                             ("date", "2025-02-29"), ("observation", " "), ("observation", 1),
                             ("evidence", ""), ("evidence", []), ("measurement", False)):
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(original)
                card = next(c for c in record["cards"] if "resolution" in c)
                card["resolution"][field] = value
                self.assertEqual({e["rule"] for e in validate(record)}, {"resolution"})
        for value in (None, [], {}, {"date": "2026-09-10"}):
            record = copy.deepcopy(original)
            next(c for c in record["cards"] if "resolution" in c)["resolution"] = value
            self.assertEqual({e["rule"] for e in validate(record)}, {"resolution"})
        record = copy.deepcopy(original)
        record.pop("measurements")
        self.assertEqual({e["rule"] for e in validate(record)}, {"resolution"})
        card = next(c for c in record["cards"] if "resolution" in c)
        card["resolution"].update(measurement=None, date="2024-02-29")
        self.assertEqual(validate(record), [])
        card.pop("resolution")
        self.assertEqual(validate(record), [])

    def test_resolution_render_preserves_decision_and_position(self):
        from render_plan import render
        from load_catalog import load_catalog
        catalog, meta = load_catalog()
        record = json.loads((ROOT / "skills/fixtures/design-resolved/record.json").read_text())
        card = next(c for c in record["cards"] if "resolution" in c)
        card["instantiation"] = "Direct assertions on the integer return."
        before = copy.deepcopy(record)
        text = render(record, catalog, meta)
        self.assertEqual(record, before)
        summary = text.split("## Summary", 1)[1].split("## Workflow", 1)[0]
        self.assertIn(" Resolution recorded 2026-09-10.\n", summary)
        prefix, uncertain = text.split("## Not verified", 1)
        resolution = card["resolution"]
        line = f'Resolution ({resolution["date"]}): {resolution["observation"]} Evidence: {resolution["evidence"]}'
        self.assertNotIn(line, prefix)
        self.assertIn(line + " Measurement: fixture-check\n", uncertain)
        self.assertLess(uncertain.index("Decision: undecided"), uncertain.index("- do_not_use_when:"))
        self.assertLess(uncertain.index("- do_not_use_when:"), uncertain.index(line))
        self.assertLess(uncertain.index(line), uncertain.index("Determinism move:"))
        self.assertLess(uncertain.index("Determinism move:"), uncertain.index("Instantiation:"))
        self.assertEqual(text, render(record, catalog, meta))
        card["resolution"]["measurement"] = None
        self.assertIn(line + "\n", render(record, catalog, meta))

    def test_citation_multiple_roots_first_match_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "first", root / "second"
            first.mkdir(); second.mkdir()
            (first / "both.txt").write_text("one\n")
            (second / "both.txt").write_text("one\ntwo\n")
            (second / "later.txt").write_text("one\n")
            absolute = str(second / "later.txt") + ":1"
            path = root / "record.json"
            path.write_text(json.dumps({"resolution": {"evidence": "later.txt:1 both.txt:1 both.txt:2 absent.txt:1 " + absolute,
                                                       "observation": "ignored.txt:99"}}))
            for kind in ("design", "audit"):
                result = self.run_script(kind, "check_citations.py", path, "--root", first, "--root", second)
                self.assertEqual(result.returncode, 3, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data["roots"], [str(first), str(second)])
                self.assertEqual(data["counts"], {"found": 3, "missing": 1, "out-of-bounds": 1, "requirements": 0, "unknown-requirement": 0})
                self.assertEqual(data["resolved"], [{"citation": "later.txt:1", "root": str(second)},
                                                    {"citation": "both.txt:1", "root": str(first)},
                                                    {"citation": absolute, "root": None}])
                self.assertEqual([c["status"] for c in data["citations"]], ["out-of-bounds", "missing"])
                reversed_result = self.run_script(kind, "check_citations.py", path, "--root", second, "--root", first)
                self.assertEqual(json.loads(reversed_result.stdout)["counts"], {"found": 4, "missing": 1, "out-of-bounds": 0, "requirements": 0, "unknown-requirement": 0})

    def test_repeated_citations_threshold_distinct_entries_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a.txt", "b.txt", "c.txt"):
                (root / name).write_text("one\n")
            path = root / "record.json"
            for kind in ("design", "audit"):
                for count in (2, 3, 4):
                    record = {"checks": [{"evidence": "b.txt:1 a.txt:1 a.txt:1 c.txt:1"} for _ in range(count)]}
                    if count == 4:
                        record["checks"][-1]["evidence"] = "b.txt:1"
                    path.write_text(json.dumps(record))
                    result = self.run_script(kind, "check_citations.py", path, "--root", root)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    data = json.loads(result.stdout)
                    expected = [] if count == 2 else ([{"citation": "b.txt:1", "entries": 4},
                        {"citation": "a.txt:1", "entries": 3}, {"citation": "c.txt:1", "entries": 3}] if count == 4 else
                        [{"citation": c + ".txt:1", "entries": 3} for c in ("a", "b", "c")])
                    self.assertEqual(data["repeated"], expected)
                    self.assertEqual(data["counts"], {"found": 3, "missing": 0, "out-of-bounds": 0, "requirements": 0, "unknown-requirement": 0})

    def test_positive_summaries_sources_and_repeatability(self):
        import re
        with tempfile.TemporaryDirectory() as tmp:
            for fixture in sorted((ROOT / "skills/fixtures").glob("*/record.json")):
                kind = "design" if fixture.parent.name.startswith("design") else "audit"
                validator = "validate_judgments.py" if kind == "design" else "validate_findings.py"
                result = self.run_script(kind, validator, fixture)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                counts = json.loads(result.stdout)
                source = fixture
                if kind == "audit":
                    source = Path(tmp) / "routed.json"
                    result = self.run_script(kind, "route_failures.py", fixture, "--output", source)
                    self.assertEqual(result.returncode, 0, result.stdout)
                output = Path(tmp) / "result.md"
                renderer = "render_plan.py" if kind == "design" else "render_findings.py"
                result = self.run_script(kind, renderer, source, "--output", output)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                text = output.read_text()
                summary = text.split("## Summary\n", 1)[1].split("\n## ", 1)[0]
                if kind == "design":
                    for key in ("apply", "reject", "undecided"):
                        self.assertIn(f'{key}: {counts[key]}', summary.lower())
                    self.assertIn(f'unknown verdicts: {counts["unknown"]}', summary)
                else:
                    self.assertIn(f'Defects: {counts["defects"]}', summary)
                    for key, count in counts["statuses"].items():
                        self.assertIn(f'- {key}: {count}\n', summary)
                    for key, count in counts["severity"].items():
                        self.assertIn(f'{key}: {count}', summary)
                _, sources = text.split("## Sources\n", 1)
                definitions = re.findall(r"^\[([^]]+)\]:", sources, re.M)
                used = re.findall(r"\[[^]\n]+\]\[([^]\n]+)\]", text)
                self.assertTrue(definitions)
                self.assertEqual(len(definitions), len(set(definitions)))
                self.assertEqual(set(definitions), set(used))
                first = output.read_bytes()
                self.run_script(kind, renderer, source, "--output", output)
                self.assertEqual(output.read_bytes(), first)

    def test_common_field_boundaries(self):
        for kind, folder, validator in (("design", "design-sound", "validate_judgments.py"),
                                        ("audit", "audit-known-defect", "validate_findings.py")):
            original = json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())
            bad_values = [("skill", None, "skill"),
                          ("skill", dict(original["skill"], version="0.0.0"), "skill"),
                          ("skill", dict(original["skill"], catalog_sha256="0" * 64), "skill"),
                          ("models", None, "models"),
                          ("models", {"generator": "unknown", "verifier": ""}, "models"),
                          ("models", {"generator": "unknown"}, "models"),
                          ("assumptions", None, "assumptions"),
                          ("assumptions", [{"topic": "x", "statement": " "}], "assumptions"),
                          ("measurements", [{"id": "m", "command": "x", "env": {}, "exit_code": True,
                                              "artifact_revision": "", "log": None, "note": ""}], "measurements"),
                          ("artifact_identity", {"revision": 4, "files": []}, "artifact-identity"),
                          ("unavailable_sources", [{"unavailable": False, "source_url": "x", "reason": "x"}], "unavailable-sources")]
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "record.json"
                for field, value, rule in bad_values:
                    record = copy.deepcopy(original); record[field] = value
                    path.write_text(json.dumps(record))
                    result = self.run_script(kind, validator, path)
                    self.assertEqual(result.returncode, 3, result.stderr)
                    self.assertIn(rule, {e["rule"] for e in json.loads(result.stdout)})

    def test_optional_fields_render_and_remain_absent_safe(self):
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
                    if present:
                        self.assertLess(text.index("Artifact identity:"), text.index("## Assumptions"))
                        self.assertLess(text.index("## Assumptions"), text.index("## Measurements"))
                        self.assertLess(text.index("## Measurements"), text.index("## Summary"))
                        self.assertIn("- probe:", text)
                        self.assertIn("1 files", text)
                        self.assertIn("a" * 64, text)
                    if kind == "design":
                        self.assertIn("Instantiation:", text)

    def test_output_path_refused_when_it_is_the_input_or_inside_the_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind, folder in (("design", "design-sound"), ("audit", "audit-known-defect")):
                skill = ROOT / "skills" / ("verification-" + kind)
                record = Path(tmp) / (kind + ".json")
                record.write_text((ROOT / "skills/fixtures" / folder / "record.json").read_text())
                if kind == "audit":
                    routed = self.run_script(kind, "route_failures.py", record)
                    self.assertEqual(routed.returncode, 0, routed.stdout + routed.stderr)
                    record.write_text(routed.stdout)
                before = record.read_bytes()
                renderer = "render_plan.py" if kind == "design" else "render_findings.py"
                scripts = [(renderer, [record]), ("check_citations.py", [record, "--root", tmp])]
                if kind == "audit":
                    scripts.append(("route_failures.py", [record]))
                for name, args in scripts:
                    for output in (record, Path(tmp) / "sub" / ".." / record.name):
                        with self.subTest(kind=kind, script=name, output=str(output)):
                            result = self.run_script(kind, name, *args, "--output", output)
                            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                            self.assertEqual(json.loads(result.stdout)[0]["rule"], "usage")
                            self.assertEqual(record.read_bytes(), before)
                    inside = skill / "assets" / "never-written.md"
                    with self.subTest(kind=kind, script=name, output="inside skill"):
                        result = self.run_script(kind, name, *args, "--output", inside)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertFalse(inside.exists())
                artifact = Path(tmp) / "artifact.txt"
                artifact.write_text("artifact\n")
                for output in (artifact, skill / "SKILL.md"):
                    with self.subTest(kind=kind, script="scaffold_record.py", output=str(output)):
                        result = self.run_script(kind, "scaffold_record.py", "--artifact", artifact, "--scope", "s", "--output", output)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(artifact.read_text(), "artifact\n")
                self.assertEqual((skill / "SKILL.md").read_text(), (ROOT / "skills" / ("verification-" + kind) / "SKILL.md").read_text())
                result = self.run_script(kind, "load_catalog.py", "--check", "--output", skill / "assets" / "never-written.json")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse((skill / "assets" / "never-written.json").exists())

    def test_checklist_pin_is_enforced_by_the_loader(self):
        import shutil
        audit = ROOT / "skills/verification-audit"
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "verification-audit"
            shutil.copytree(audit, copy)
            catalog, meta = checker.loader.load_catalog(copy)
            self.assertEqual(meta["name"], "verification-audit")
            self.assertIn("checklist_sha256", checker.loader.skill_pins(meta))
            checklist = copy / checker.loader.CHECKLIST_PATH
            checklist.write_text(checklist.read_text() + "\n- An extra question nobody pinned.\n")
            with self.assertRaises(checker.loader.SnapshotError):
                checker.loader.load_catalog(copy)
            checklist.unlink()
            with self.assertRaises(checker.loader.SnapshotError):
                checker.loader.load_catalog(copy)
            design = Path(tmp) / "verification-design"
            shutil.copytree(ROOT / "skills/verification-design", design)
            self.assertNotIn("checklist_sha256", checker.loader.skill_pins(checker.loader.load_catalog(design)[1]))
            shutil.copy(audit / checker.loader.CHECKLIST_PATH, design / "references" / "principles-checklist.md")
            with self.assertRaises(checker.loader.SnapshotError):
                checker.loader.load_catalog(design)

    def test_rendered_header_names_skill_pins_and_model_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind, folder, renderer in (("design", "design-sound", "render_plan.py"), ("audit", "audit-known-defect", "render_findings.py")):
                record = json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())
                record["models"] = {"generator": "Family G", "verifier": "Family V"}
                path, output = Path(tmp) / "record.json", Path(tmp) / "out.md"
                path.write_text(json.dumps(record))
                if kind == "audit":
                    path.write_text(self.run_script(kind, "route_failures.py", path).stdout)
                result = self.run_script(kind, renderer, path, "--output", output)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                head = output.read_text().split("## Assumptions", 1)[0]
                self.assertIn(f'Skill: verification-{kind} {record["skill"]["version"]}', head)
                for key, value in record["skill"].items():
                    if key.endswith("_sha256"):
                        self.assertIn(f'{key.removesuffix("_sha256")} `{value}`', head)
                self.assertIn("Generator model: Family G", head)
                self.assertIn("Verifier model: Family V", head)

    def test_outside_observation_cannot_replace_coverage_or_route(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            for mutation, rule in (({"free": False}, "coverage"), ({"cards": []}, "routing"),
                                   ({"failure": "unmapped"}, "failure")):
                bad = copy.deepcopy(record)
                bad["checks"][-1].update(mutation)
                path.write_text(json.dumps(bad))
                result = self.run_script("audit", "validate_findings.py", path)
                self.assertEqual(result.returncode, 3)
                self.assertIn(rule, {e["rule"] for e in json.loads(result.stdout)})


if __name__ == "__main__":
    unittest.main()
