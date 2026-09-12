"""Inventory RT: pinned routing and record/output preservation."""
import copy
import json
from support import ROOT, ScriptCase, fixture, module


class RoutingTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.route = module("route_failures").route
        self.catalog = module("load_catalog").load_catalog()[0]

    def test_rt_1_validation_before_output(self):
        record = fixture()
        record["checks"].pop(0)
        self.assert_rules(self.call("audit", "route_failures.py", record, "--output", self.output), {"coverage"})
        self.assertFalse(self.output.exists())
        self.output.write_text("preserve existing output")
        self.assert_rules(self.call("audit", "route_failures.py", record, "--output", self.output), {"coverage"})
        self.assertEqual(self.output.read_text(), "preserve existing output")

    def test_rt_2_all_mapped_candidates(self):
        cards = {c["id"]: c for c in self.catalog["cards"]}
        for failure in self.catalog["failures"]:
            record = fixture()
            check = next(c for c in record["checks"] if c["status"] == "defect")
            index = record["checks"].index(check)
            check["failure"] = failure["failure"]
            check.pop("related_cards", None)
            result = self.call("audit", "route_failures.py", record)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            routed = json.loads(result.stdout)["checks"][index]
            self.assertIs(routed["routed"], True)
            self.assertEqual(routed["cards"], [{k: cards[cid][k] for k in ("id", "title", "html_url", "source_url")} for cid in failure["cards"]])

    def test_rt_4_recompute_and_strip_nondefects(self):
        record = fixture()
        expected = self.route(record, self.catalog)
        for check in record["checks"]:
            check.update(cards=[{"id": "stale/card"}], routed="stale")
        self.assertEqual(self.route(record, self.catalog), expected)
        for check in expected["checks"]:
            if check["status"] != "defect":
                self.assertNotIn("cards", check)
                self.assertNotIn("routed", check)

    def test_rt_5_deep_copy_preserves_other_fields(self):
        """code-only: routing cannot mutate the input or share its nested objects."""
        record = fixture()
        record["extension"] = {"nested": ["original"]}
        before = copy.deepcopy(record)
        routed = self.route(record, self.catalog)
        self.assertEqual(record, before)
        stripped = copy.deepcopy(routed)
        for check in stripped["checks"]:
            check.pop("cards", None)
            check.pop("routed", None)
        self.assertEqual(stripped, before)
        routed["extension"]["nested"].append("changed")
        routed["checks"][0]["evidence"] = "changed"
        self.assertEqual(record, before)

    def test_rt_6_json_output_and_refusal(self):
        record = fixture()
        stdout = self.call("audit", "route_failures.py", record)
        self.assertEqual(stdout.returncode, 0, stdout.stdout + stdout.stderr)
        self.assertEqual(json.loads(stdout.stdout), self.route(record, self.catalog))
        result = self.run_script("audit", "route_failures.py", self.record, "--output", self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), {"output": str(self.output)})
        self.assertEqual(json.loads(self.output.read_text()), json.loads(stdout.stdout))
        self.assert_refused("audit", "route_failures.py", [self.record], self.record)
    def test_rt_3_unmapped_defect_routes_to_no_card(self):
        record = json.loads((ROOT / "skills/fixtures/audit-missing-evidence/record.json").read_text())
        record["checks"].append({"free": True, "principle": 5, "question": "Does the report preserve the criterion identifier?", "status": "defect", "evidence": "Illustrative report row omits its criterion identifier.", "failure": "unmapped", "failure_note": "Missing criterion identifier in the emitted row.", "severity": "low"})
        routed = self.call("audit", "route_failures.py", record)
        self.assertEqual(routed.returncode, 0, routed.stdout + routed.stderr)
        routed_record = json.loads(routed.stdout)
        self.assertEqual(routed_record["checks"][-1]["cards"], [])
        self.assertIs(routed_record["checks"][-1]["routed"], False)

