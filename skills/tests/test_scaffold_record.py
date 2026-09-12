"""Inventory AS and DS: unfilled scaffolds and output boundaries."""
import json
import re
from support import AUDIT, ScriptCase, module


class ScaffoldTests(ScriptCase):
    def scaffold(self, kind, output="-"):
        result = self.run_script(kind, "scaffold_record.py", "--artifact", "test artifact", "--scope", "test scope", "--output", output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_as_1_checklist_verbatim_and_unfilled(self):
        record = self.scaffold("audit")["record"]
        expected = []
        for line in (AUDIT / "references/principles-checklist.md").read_text().splitlines():
            match = re.fullmatch(r"## Principle ([1-9])", line)
            if match:
                principle = int(match[1])
            elif line.startswith("- "):
                expected.append((principle, line[2:]))
        self.assertEqual([(c["principle"], c["question"]) for c in record["checks"]], expected)
        self.assertTrue(expected)
        for check in record["checks"]:
            self.assertEqual(check["status"], "")
            self.assertEqual(check["evidence"], "")
        self.assert_rules(self.call("audit", "validate_findings.py", record), {"status", "evidence", "models"})

    def identity(self, kind):
        record = self.scaffold(kind)["record"]
        loader = module("load_catalog", kind)
        catalog, meta = loader.load_catalog()
        self.assertEqual(record["artifact"], "test artifact")
        self.assertEqual(record["scope"], "test scope")
        self.assertEqual(record["corpus_revision"], catalog["revision"])
        self.assertEqual(record["skill"], loader.skill_pins(meta))
        return record

    def test_as_2_identity_and_arguments(self):
        self.assertEqual(self.identity("audit")["models"], {"generator": "", "verifier": ""})

    def counts(self, kind):
        envelope = self.scaffold(kind)
        expected = {"checks": 18} if kind == "audit" else {"cards": 17, "conditions": 156}
        self.assertEqual(set(envelope), {"record", "counts"})
        self.assertEqual(envelope["counts"], expected)
        receipt = self.scaffold(kind, self.output)
        self.assertEqual(receipt, {"output": str(self.output), "counts": expected})
        self.assertEqual(json.loads(self.output.read_text()), envelope["record"])

    def test_as_3_stdout_and_file_counts(self):
        self.counts("audit")

    def test_as_4_missing_destination_directory(self):
        target = self.root / "dated/run/record.json"
        self.scaffold("audit", target)
        self.assertTrue(target.is_file())
        self.assertEqual(json.loads(target.read_text())["artifact"], "test artifact")

    def refusal(self, kind):
        self.record.write_text("artifact input\n")
        self.assert_refused(kind, "scaffold_record.py", ["--artifact", self.record, "--scope", "test scope"], self.record)

    def test_as_5_refused_output(self):
        self.refusal("audit")

    def test_ds_1_catalog_order_and_blank_conditions(self):
        record = self.scaffold("design")["record"]
        catalog = module("load_catalog", "design").load_catalog()[0]
        self.assertEqual([c["id"] for c in record["cards"]], [c["id"] for c in catalog["cards"]])
        for card, source in zip(record["cards"], catalog["cards"]):
            for group in ("use_when", "do_not_use_when"):
                self.assertEqual(card[group], [dict(condition=text, verdict="", evidence="") for text in source[group]])

    def test_ds_2_empty_judgment_placeholders(self):
        record = self.scaffold("design")["record"]
        self.assertEqual(record["models"], {"generator": "", "verifier": ""})
        self.assertEqual(record["assumptions"], [{"topic": "verification-path", "statement": ""}])
        self.assertEqual(record["plan"], {"design": "", "requirements": []})
        self.assertEqual(record["workflow"], dict(generated="", generator="", completion_signal="", self_review_points=[]))
        for card in record["cards"]:
            self.assertEqual(card["decision"], "")
            self.assertEqual(card["reason"], "")
            self.assertNotIn("resolution", card)
        self.assert_rules(self.call("design", "validate_judgments.py", record), {"assumptions", "structure", "models", "plan"})

    def test_ds_3_identity_and_arguments(self):
        self.identity("design")

    def test_ds_4_stdout_and_file_counts(self):
        self.counts("design")

    def test_ds_5_refused_output(self):
        self.refusal("design")
