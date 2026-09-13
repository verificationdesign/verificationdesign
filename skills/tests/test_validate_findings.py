"""Behavior contract VF-1 through VF-17, using isolated positive records."""
import copy
import json
from support import ScriptCase, fixture, module


class ValidateFindingsTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.v = module("validate_findings")
        self.good = fixture()
        self.assertEqual(self.v.validate(self.good), [])

    def rules(self, record, expected):
        self.assertEqual({e["rule"] for e in self.v.validate(record)}, set(expected))

    def change(self, index, key, value, rule):
        record = copy.deepcopy(self.good)
        record["checks"][index][key] = value
        self.rules(record, {rule})

    def test_vf_1_record_structure(self):
        for value in (None, [], "record"):
            self.rules(value, {"structure"})
        for key in ("artifact", "scope", "corpus_revision", "checks"):
            for value in (None, "", " ", 4):
                record = copy.deepcopy(self.good)
                record[key] = value
                self.rules(record, {"structure"})
            record = copy.deepcopy(self.good)
            del record[key]
            self.rules(record, {"structure"})
        for key, value in (("corpus_revision", "a" * 40), ("scope", "one\ntwo")):
            record = copy.deepcopy(self.good)
            record[key] = value
            self.rules(record, {"structure"})

    def test_vf_2_check_structure(self):
        # Use an additional free entry so malformed rows do not remove coverage.
        for value in (None, [], "row"):
            record = copy.deepcopy(self.good)
            record["checks"].append(value)
            self.rules(record, {"structure"})
        for key, values in (("question", (None, "", " ", 3)),
                            ("principle", (True, "1", 0, 10, []))):
            for value in values:
                self.change(-1, key, value, "structure")

    def test_vf_3_exact_coverage(self):
        record = copy.deepcopy(self.good)
        record["checks"].pop(0)
        self.rules(record, {"coverage"})
        record = copy.deepcopy(self.good)
        record["checks"].append(copy.deepcopy(record["checks"][0]))
        self.rules(record, {"coverage"})
        self.change(0, "question", "altered question", "coverage")
        self.change(0, "principle", 2, "coverage")

    def test_vf_4_free_contract(self):
        for value in (1, "true", None):
            self.change(0, "free", value, "structure")
        record = copy.deepcopy(self.good)
        extra = copy.deepcopy(record["checks"][2])
        extra["free"] = True
        record["checks"].append(extra)
        self.rules(record, {"coverage"})
        extra["question"] = "Original extra question"
        self.rules(record, set())
        extra.update(status="sound", severity=None)
        extra.pop("related_cards")
        self.rules(record, {"coverage"})

    def test_vf_5_outside_coverage(self):
        self.change(-1, "free", False, "coverage")
        record = copy.deepcopy(self.good)
        record["checks"][0].update(status="out-of-scope", free=True)
        self.rules(record, {"coverage"})

    def test_vf_6_statuses(self):
        for status in ("sound", "not-applicable", "not-checked", "insufficient-evidence"):
            record = copy.deepcopy(self.good)
            record["checks"][0]["status"] = status
            self.rules(record, set())
        for status in ("unknown", None, [], 1):
            self.change(0, "status", status, "status")

    def test_vf_7_evidence_all_statuses(self):
        for status in ("defect", "sound", "not-applicable", "not-checked", "insufficient-evidence", "out-of-scope"):
            for value in (None, "", " ", 1):
                record = copy.deepcopy(self.good)
                index = 2 if status == "defect" else -1 if status == "out-of-scope" else 0
                record["checks"][index].update(status=status, evidence=value)
                self.rules(record, {"evidence"})

    def test_vf_8_failure_values(self):
        for value in ([], None, 1, "unknown"):
            self.change(2, "failure", value, "failure")
        record = copy.deepcopy(self.good)
        record["checks"][2]["failure"] = "unmapped"
        self.rules(record, set())

    def test_vf_9_failure_notes(self):
        for value in (None, 1, []):
            self.change(0, "failure_note", value, "failure")
        for value in (None, "", " "):
            record = copy.deepcopy(self.good)
            record["checks"][2].update(failure="unmapped", failure_note=value)
            self.rules(record, {"failure"})
        record["checks"][2].pop("failure_note")
        self.rules(record, {"failure"})

    def test_vf_10_defect_severity(self):
        for value in (None, "critical", "", 1):
            self.change(2, "severity", value, "severity")
        for value in ("high", "medium", "low"):
            record = copy.deepcopy(self.good)
            record["checks"][2]["severity"] = value
            self.rules(record, set())

    def test_vf_11_nondefect_severity(self):
        for status in ("sound", "not-applicable", "not-checked", "insufficient-evidence", "out-of-scope"):
            for missing in (False, True):
                record = copy.deepcopy(self.good)
                check = record["checks"][-1 if status == "out-of-scope" else 0]
                check["status"] = status
                if missing:
                    del check["severity"]
                else:
                    check["severity"] = "low"
                self.rules(record, {"severity"})

    def test_vf_12_inapplicable_routing(self):
        for status in ("not-applicable", "out-of-scope"):
            for key, value, rule in (("failure", "unmapped", "failure"), ("failure_note", "note", "failure"),
                                     ("cards", [], "routing"), ("routed", False, "routing")):
                record = copy.deepcopy(self.good)
                record["checks"][-1 if status == "out-of-scope" else 0].update(status=status, **{key: value})
                self.rules(record, {rule})

    def test_vf_13_related_candidates(self):
        self.change(0, "related_cards", [], "routing")
        self.change(2, "related_cards", ["verification/comparator"], "routing")

    def test_vf_14_related_list(self):
        for value in (None, "verification/blind-oracle", [1], ["absent"], ["verification/blind-oracle"] * 2):
            self.change(2, "related_cards", value, "routing")

    def test_vf_15_checklist_structure(self):
        """code-only: malformed packaged checklist inputs."""
        good = "\n".join(f"## Principle {p}\n- Q{p}a\n- Q{p}b" for p in range(1, 10))
        path = self.root / "checklist.md"
        path.write_text(good)
        self.assertEqual(len(self.v.checklist(path)), 18)
        for bad in ("- orphan\n" + good, good.replace("- Q1b", ""), good.replace("Q2b", "Q1a")):
            path.write_text(bad)
            with self.assertRaises(self.v.SnapshotError):
                self.v.checklist(path)

    def test_vf_16_error_envelope(self):
        record = copy.deepcopy(self.good)
        record["checks"][0]["evidence"] = ""
        result = self.call("audit", "validate_findings.py", record)
        self.assert_rules(result, {"evidence"})
        self.assertEqual(json.loads(result.stdout), [{"card": None, "check": 0, "rule": "evidence",
            "message": "every status requires evidence or a reason stating what is missing"}])
        self.assertEqual(result.stderr, "findings validation failed\n")

    def test_vf_17_success_counts(self):
        for folder in ("audit-known-defect", "audit-missing-evidence"):
            from support import ROOT
            record = json.loads((ROOT / "skills/fixtures" / folder / "record.json").read_text())
            result = self.call("audit", "validate_findings.py", record)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            checks = record["checks"]
            self.assertEqual(json.loads(result.stdout), {"valid": True, "checks": len(checks),
                "defects": sum(c["status"] == "defect" for c in checks),
                "statuses": {s: sum(c["status"] == s for c in checks) for s in
                    ("defect", "sound", "not-applicable", "not-checked", "insufficient-evidence", "out-of-scope")},
                "severity": {s: sum(c["status"] == "defect" and c["severity"] == s for c in checks)
                    for s in ("high", "medium", "low")}, "warnings": []})

    def grouped_record(self):
        record = copy.deepcopy(self.good)
        for index in (3, 4):
            record["checks"][index].update(status="defect", severity="low", failure="unmapped",
                                            failure_note="Shared missing record", evidence="Same evidence")
        record["cause_groups"] = [{"cause": "Shared missing record", "checks": [3, 4]}]
        return record

    def test_cause_groups_structure(self):
        record = self.grouped_record()
        self.rules(record, set())
        invalid = [None, {}, "groups", [None], [{"cause": "", "checks": [3, 4]}],
                   [{"cause": "shared"}], [{"cause": "shared", "checks": [3, 4], "extra": True}]]
        invalid += [[{"cause": "shared", "checks": members}] for members in
                    (None, "3,4", [], [3], [3, 3], [3, 0], [3, -1], [3, 999],
                     [3, True], [3, "4"], [3, 4.0], [3, []])]
        invalid += [[{"cause": "first", "checks": [2, 3]},
                     {"cause": "second", "checks": [3, 4]}]]
        for groups in invalid:
            with self.subTest(groups=groups):
                record["cause_groups"] = groups
                self.rules(record, {"cause-groups"})
        result = self.call("audit", "validate_findings.py", record)
        self.assert_rules(result, {"cause-groups"})

    def test_identical_evidence_warning_is_advisory(self):
        record = self.grouped_record()
        before = copy.deepcopy(record)
        for grouped in (True, False):
            if not grouped:
                record.pop("cause_groups")
            result = self.call("audit", "validate_findings.py", record)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["warnings"], [{"rule": "identical-defect-evidence", "checks": [3, 4],
                "message": "Byte-identical evidence suggests a shared cause but does not establish one."}])
            self.assertEqual(report["defects"], 3)
        self.assertEqual(record["checks"], before["checks"])
        record["checks"][4]["evidence"] += " "
        self.assertEqual(self.v.warnings(record), [])
        record["checks"][0]["evidence"] = record["checks"][3]["evidence"]
        self.assertEqual(self.v.warnings(record), [])

    def test_no_cause_groups_remains_valid(self):
        for groups in (None, []):
            record = copy.deepcopy(self.good)
            if groups is not None:
                record["cause_groups"] = groups
            result = self.call("audit", "validate_findings.py", record)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["warnings"], [])
