"""Behavior contract FF-1 through FF-12."""
import copy
import json
import re
from support import ScriptCase, ROOT, fixture, module


class RenderFindingsTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.r = module("render_findings")
        self.catalog, self.meta = self.r.load_catalog()
        self.good = fixture()

    def render(self, record):
        self.assertEqual(self.r.validate(record, self.catalog, meta=self.meta), [])
        return self.r.render(self.r.route(record, self.catalog), self.catalog, self.meta)

    def section(self, text, name):
        return text.split("## " + name + "\n", 1)[1].split("\n## ", 1)[0]

    def test_ff_1_invalid_no_write(self):
        record = copy.deepcopy(self.good)
        record["checks"][0]["evidence"] = ""
        result = self.call("audit", "render_findings.py", record, "--output", self.output)
        self.assert_rules(result, {"evidence"})
        self.assertFalse(self.output.exists())

    def test_ff_2_automatic_routing(self):
        for folder in ("audit-known-defect", "audit-missing-evidence"):
            record = json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())
            before = copy.deepcopy(record)
            first = self.call("audit", "render_findings.py", record)
            second = self.call("audit", "render_findings.py", self.r.route(record, self.catalog))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(record, before)

    def test_ff_4_summary(self):
        record = copy.deepcopy(self.good)
        record["checks"][2]["failure"] = "unmapped"
        summary = self.section(self.render(record), "Summary")
        checks = record["checks"]
        severities = {s: sum(c["status"] == "defect" and c["severity"] == s for c in checks) for s in ("high", "medium", "low")}
        self.assertIn("Defects: 1. " + "; ".join(f"{s}: {n}" for s, n in severities.items()) + ".", summary.splitlines())
        for status in ("defect", "sound", "not-applicable", "not-checked", "insufficient-evidence", "out-of-scope"):
            self.assertIn(f'- {status}: {sum(c["status"] == status for c in checks)}', summary.splitlines())
        self.assertIn("- " + re.sub(r" \[Principles\]\([^)]+\)", "", checks[2]["question"]), summary.splitlines())
        self.assertEqual(self.section(self.render(self.good), "Summary").split("Unmapped defects:")[1].strip(), "None.")

    def test_ff_5_sections(self):
        text = self.render(self.good)
        names = ("Defects", "Checked and sound", "Not applicable", "Not checked", "Insufficient evidence", "Observed outside scope")
        headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual([n for n in headings if n in names], list(names))
        for name in ("Checked and sound", "Insufficient evidence"):
            self.assertEqual(self.section(text, name).strip(), "None.")

    def test_ff_6_check_order(self):
        """code-only: scrambled input and additional questions preserve reading order."""
        record = copy.deepcopy(self.good)
        record["checks"] = [c for c in record["checks"] if not c.get("free")]
        for i, check in enumerate(record["checks"]):
            check.update(status="defect", severity="low", failure="unmapped", failure_note="note", evidence=f"unique {i}")
            check.pop("related_cards", None)
        extras = []
        for question in ("Z free", "A free"):
            extra = copy.deepcopy(record["checks"][0])
            extra.update(free=True, question=question, evidence=question)
            extras.append(extra)
        expected = record["checks"][:2] + list(reversed(extras)) + record["checks"][2:]
        record["checks"] = list(reversed(record["checks"] + extras))
        text = self.section(self.render(record), "Defects")
        self.assertEqual([line for line in text.splitlines() if line.startswith("Evidence: ")],
                         ["Evidence: " + c["evidence"] for c in expected])

    def test_ff_7_labels_and_principles(self):
        record = copy.deepcopy(self.good)
        record["checks"][0]["status"] = "sound"
        record["checks"][1]["status"] = "insufficient-evidence"
        text = self.render(record)
        headings = {"defect": "Defects", "sound": "Checked and sound", "not-applicable": "Not applicable",
                    "not-checked": "Not checked", "insufficient-evidence": "Insufficient evidence", "out-of-scope": "Observed outside scope"}
        for c in record["checks"]:
            lines = self.section(text, headings[c["status"]]).splitlines()
            label = "Evidence" if c["status"] in ("sound", "defect") else "Reason"
            self.assertIn(label + ": " + c["evidence"], lines)
            self.assertIn(re.sub(r"\[Principles\]\([^)]+\)", f'[Principles][p{c["principle"]}]', c["question"]), lines)
            for url in re.findall(r"\[Principles\]\(([^)]+)\)", c["question"]):
                self.assertIn(f'[p{c["principle"]}]: {url}', text.splitlines())

    def test_ff_8_defect_fields(self):
        for failure in (self.good["checks"][2]["failure"], "unmapped"):
            record = copy.deepcopy(self.good)
            c = record["checks"][2]
            c.update(failure=failure, failure_note="A specific explanatory note.")
            lines = self.section(self.render(record), "Defects").splitlines()
            for field, label in (("severity", "Severity"), ("failure", "Failure"), ("failure_note", "Failure note")):
                self.assertIn(label + ": " + c[field], lines)

    def test_ff_10_unavailable_placement(self):
        record = copy.deepcopy(self.good)
        unavailable = {"unavailable": True, "source_url": "https://example.invalid/source", "reason": "offline"}
        record["unavailable_sources"] = [unavailable]
        text = self.render(record)
        section = self.section(text, "Insufficient evidence")
        payload = section.split("```json\n")[1].split("```", 1)[0]
        self.assertEqual(json.loads(payload), unavailable)
        self.assertEqual(text.count(unavailable["source_url"]), 1)

    def test_ff_11_output_boundary(self):
        self.record.write_text(json.dumps(self.good))
        self.assert_refused("audit", "render_findings.py", [self.record], self.record)

    def test_ff_12_envelope_and_stability(self):
        before = copy.deepcopy(self.good)
        result = self.call("audit", "render_findings.py", self.good)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(set(envelope), {"text"})
        self.assertEqual(envelope["text"], self.render(self.good))
        for attempt in range(2):
            result = self.call("audit", "render_findings.py", self.good, "--output", self.output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.output.read_bytes(), envelope["text"].encode("utf-8"))
        self.assertEqual(self.good, before)

    def test_ff_9_unmapped_no_card(self):
        record = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        record["checks"].append({"free": True, "principle": 5, "question": "Does the report preserve the criterion identifier?", "status": "defect", "evidence": "Illustrative report row omits its criterion identifier.", "failure": "unmapped", "failure_note": "Missing criterion identifier in the emitted row.", "severity": "low"})
        routed = self.call("audit", "route_failures.py", record)
        self.assertEqual(routed.returncode, 0, routed.stdout + routed.stderr)
        routed_record = json.loads(routed.stdout)
        rendered = self.call("audit", "render_findings.py", routed_record, * ("--output", self.output))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("No routed card: outside the six mapped failures; see the failure note above.", text)
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["## Assumptions", "## Summary", "## Defects", "## Checked and sound", "## Not applicable", "## Not checked", "## Insufficient evidence", "## Observed outside scope", "## Sources"])

    def test_ff_9_judged_candidates(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        defect = next(c for c in record["checks"] if c["status"] == "defect")
        self.assertEqual(defect["related_cards"], ["verification/blind-oracle"])
        rendered = self.call("audit", "render_findings.py", record, * ("--output", self.output))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("Candidate cards from the failure map (a lookup, not an applicability judgment):", text)
        self.assertIn("- judged applicable: [Blind Oracle]", text)
        self.assertIn("- candidate: [Cross-Family]", text)
        self.assertIn("Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).", text)
        defect["related_cards"] = ["verification/comparator"]
        result = self.call("audit", "validate_findings.py", record)
        self.assertEqual(result.returncode, 3)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"routing"})
        non_defect = next(c for c in record["checks"] if c["status"] == "not-checked")
        defect["related_cards"] = ["verification/blind-oracle"]
        non_defect["related_cards"] = ["verification/blind-oracle"]
        result = self.call("audit", "validate_findings.py", record)
        self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"routing"})

    def test_ff_9_unmapped_judgment(self):
        record = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        record["checks"].append({"free": True, "principle": 5, "question": "Does the report preserve the criterion identifier?", "status": "defect", "evidence": "Illustrative report row omits its criterion identifier.", "failure": "unmapped", "failure_note": "Missing criterion identifier in the emitted row.", "severity": "low", "related_cards": ["context-and-state/constitution"]})
        rendered = self.call("audit", "render_findings.py", record, * ("--output", self.output))
        self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
        text = self.output.read_text()
        self.assertIn("Cards named by judgment (the failure map has no entry for this defect):", text)
        self.assertIn("- judged applicable: [Constitution]", text)

    def test_ff_3_tampered_routing(self):
        record = json.loads((ROOT / "skills/fixtures/audit-known-defect/record.json").read_text())
        routed = self.call("audit", "route_failures.py", record)
        self.assertEqual(routed.returncode, 0)
        record = json.loads(routed.stdout)
        defect = next(c for c in record["checks"] if c["status"] == "defect")
        defect["cards"][0]["source_url"] = "https://example.invalid/mutable"
        result = self.call("audit", "render_findings.py", record, * ("--output", self.output))
        self.assertEqual(result.returncode, 3)
        self.assert_rules(result, {"routing"})
        self.assertFalse(self.output.exists())

    def test_free_observations_keep_record_order(self):
        record = copy.deepcopy(self.good)
        outside = copy.deepcopy(record["checks"][-1])
        record["checks"] = list(reversed(record["checks"][:-1]))
        for question in ("Z observation", "A observation", "M observation"):
            extra = copy.deepcopy(outside)
            extra.update(principle=None, question=question, evidence=question)
            record["checks"].append(extra)
        section = self.section(self.render(record), "Observed outside scope")
        self.assertEqual([line for line in section.splitlines() if line.startswith("Reason: ")],
                         ["Reason: Z observation", "Reason: A observation", "Reason: M observation"])

    def test_cause_group_summary_keeps_separate_figures(self):
        record = copy.deepcopy(self.good)
        for index in (3, 4):
            record["checks"][index].update(status="defect", severity="low", failure="unmapped",
                                            failure_note="Shared missing record", evidence="Same evidence")
        before = copy.deepcopy(record["checks"])
        for groups, count, ungrouped in ((None, 0, 3), ([], 0, 3),
                ([{"cause": "Shared missing record", "checks": [3, 4]}], 1, 1)):
            if groups is not None:
                record["cause_groups"] = groups
            text = self.render(record)
            self.assertIn(f"Author-assigned cause groups: {count}; ungrouped defect rows: {ungrouped}.",
                          self.section(text, "Summary").splitlines())
            self.assertEqual(self.section(text, "Defects").count("Severity: "), 3)
            self.assertEqual(record["checks"], before)
        empty = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        self.assertIn("Author-assigned cause groups: 0; ungrouped defect rows: 0.", self.render(empty))
