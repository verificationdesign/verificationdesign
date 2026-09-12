"""Inventory CC: citation syntax, accounting, ordering and CLI boundaries."""
import json
from pathlib import Path
import tempfile
from support import ScriptCase, module


class CitationTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.check = module("check_citations").check
        (self.root / "sample.txt").write_text("one\ntwo\nthree", encoding="utf-8")

    def report(self, record):
        return self.check(record, [str(self.root)])

    def test_cc_1_nested_selected_fields(self):
        for field in ("evidence", "reason", "statement", "note", "instantiation"):
            with self.subTest(field=field):
                report = self.report({"nested": [{field: ["sample.txt:1"]}], "question": "missing.txt:1",
                                      "command": "missing.txt:2", "observation": "missing.txt:3", "id": "missing.txt:4"})
                self.assertEqual(report["counts"], dict(found=1, missing=0, **{"out-of-bounds": 0, "requirements": 0, "unknown-requirement": 0}))
                self.assertEqual(report["citations"], [])
                self.assertEqual(report["resolved"], [{"citation": "sample.txt:1", "root": str(self.root)}])

    def test_cc_2_dot_or_slash_syntax(self):
        (self.root / "folder").mkdir()
        (self.root / "folder/file").write_text("one\ntwo\n")
        (self.root / "plain").write_text("one\n")
        report = self.report({"evidence": "sample.txt:1 sample.txt:2-3 folder/file:1-2 plain:1 time:23 V1:2 sample.txt:no"})
        self.assertEqual(report["counts"], dict(found=3, missing=0, **{"out-of-bounds": 0, "requirements": 0, "unknown-requirement": 0}))
        self.assertEqual([r["citation"] for r in report["resolved"]], ["sample.txt:1", "sample.txt:2-3", "folder/file:1-2"])

    def test_cc_4_distinct_counts_and_bounds(self):
        citations = ["sample.txt:1", "missing.txt:1", "sample.txt:0", "sample.txt:3-2", "sample.txt:4", "sample.txt:2-4"]
        report = self.report({"evidence": " ".join(citations * 2), "note": " ".join(citations)})
        self.assertEqual(report["counts"], dict(found=1, missing=1, **{"out-of-bounds": 4, "requirements": 0, "unknown-requirement": 0}))
        self.assertEqual(report["citations"], [dict(citation=c, entry="$.evidence", status="missing" if i == 0 else "out-of-bounds")
                                                for i, c in enumerate(citations[1:])])

    def test_cc_5_failure_entries_and_first_seen_order(self):
        record = {"nested": [{"note": "missing-z.txt:1 sample.txt:3 sample.txt:5"}],
                  "reason": "missing-a.txt:1 sample.txt:1 missing-z.txt:1"}
        report = self.report(record)
        self.assertEqual(report["roots"], [str(self.root)])
        self.assertEqual(report["citations"], [dict(citation="missing-z.txt:1", entry="$.nested[0].note", status="missing"),
             dict(citation="sample.txt:5", entry="$.nested[0].note", status="out-of-bounds"),
             dict(citation="missing-a.txt:1", entry="$.reason", status="missing")])
        self.assertEqual(report["resolved"], [dict(citation=c, root=str(self.root)) for c in ("sample.txt:3", "sample.txt:1")])

    def test_cc_7_requirement_ids_and_failures(self):
        for field in ("evidence", "statement"):
            report = self.report({"plan": {"requirements": [{"id": "V1"}]}, field: "V1 V9 V0 v1 V01 XV2"})
            self.assertEqual(report["counts"], dict(found=0, missing=0, **{"out-of-bounds": 0, "requirements": 1, "unknown-requirement": 1}))
            self.assertEqual(report["citations"], [dict(citation="V9", entry="$." + field, status="unknown-requirement")])
        self.assertEqual(self.report({"evidence": "V9"})["citations"], [])

    def test_cc_8_exit_codes(self):
        for evidence, code in (("sample.txt:1-3", 0), ("missing.txt:1", 3), ("sample.txt:4", 3)):
            result = self.call("audit", "check_citations.py", {"evidence": evidence}, "--root", self.root)
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_cc_9_no_citations(self):
        result = self.call("audit", "check_citations.py", {"evidence": "No citation here."}, "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), dict(counts=dict(found=0, missing=0, **{"out-of-bounds": 0, "requirements": 0,
                         "unknown-requirement": 0}), citations=[], roots=[str(self.root)], resolved=[], repeated=[]))

    def test_cc_10_requirement_dedup_per_string(self):
        """code-only: repeated ids count once per scanned string."""
        report = self.report({"plan": {"requirements": [{"id": "V1"}]}, "evidence": "V1 V1 V9 V9", "nested": {"note": "V1 V9"}})
        self.assertEqual(report["counts"], dict(found=0, missing=0, **{"out-of-bounds": 0, "requirements": 2, "unknown-requirement": 2}))
        self.assertEqual(report["citations"], [dict(citation="V9", entry=e, status="unknown-requirement") for e in ("$.evidence", "$.nested.note")])

    def test_cc_11_json_file_and_receipt(self):
        record = {"evidence": "sample.txt:1"}
        result = self.call("audit", "check_citations.py", record, "--root", self.root, "--output", self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), {"output": str(self.output)})
        self.assertEqual(json.loads(self.output.read_text()), self.report(record))

    def test_cc_12_refused_output(self):
        self.record.write_text('{"evidence": "sample.txt:1"}')
        self.assert_refused("audit", "check_citations.py", [self.record, "--root", self.root], self.record)
    def test_cc_3_ordered_roots_and_absolute_paths(self):
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
            for kind in ("audit",):
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


    def test_cc_6_repeated_distinct_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a.txt", "b.txt", "c.txt"):
                (root / name).write_text("one\n")
            path = root / "record.json"
            for kind in ("audit",):
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


