"""Inventory CF: isolated common-field validation from positive records."""
import copy
from support import ScriptCase, fixture, module


class RecordFieldsTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.common = module("record_fields")
        self.meta = module("load_catalog").load_catalog()[1]
        self.original = fixture()
        self.assertEqual(self.errors(self.original), set())

    def errors(self, record, design=False):
        errors = []
        self.common.validate_common(record, lambda card, rule, message: errors.append(rule), self.meta, design=design)
        return set(errors)

    def variants(self, field, values, rule):
        for value in values:
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.original)
                record[field] = value
                self.assertEqual(self.errors(record), {rule})

    def measurement(self):
        return dict(id="m", command="check", env={"MODE": "test"}, exit_code=0,
                    artifact_revision="rev", log=None, note="", kind="execution")

    def test_cf_1_exact_identity(self):
        good = self.original["skill"]
        values = [None, {}, dict(good, extra="x")]
        for key in good:
            values += [{k: v for k, v in good.items() if k != key}, dict(good, **{key: "wrong"})]
        self.variants("skill", values, "skill")

    def test_cf_2_missing_or_blank_models(self):
        self.variants("models", [None, [], {}, {"generator": "G"}, {"verifier": "V"},
                               {"generator": "G", "verifier": " "}, {"generator": "", "verifier": "V"},
                               {"generator": 7, "verifier": "V"}], "models")
        record = copy.deepcopy(self.original)
        del record["models"]
        self.assertEqual(self.errors(record), {"models"})

    def test_cf_3_extra_model_key(self):
        """code-only: the model object has exactly two keys."""
        self.variants("models", [dict(self.original["models"], extra="X")], "models")

    def test_cf_4_assumptions_shape(self):
        self.variants("assumptions", [None, {}, [None], [{"topic": "t"}], [{"statement": "s"}],
                                     [{"topic": " ", "statement": "s"}], [{"topic": "t", "statement": " "}],
                                     [{"topic": 1, "statement": "s"}]], "assumptions")
        record = copy.deepcopy(self.original)
        del record["assumptions"]
        self.assertEqual(self.errors(record), {"assumptions"})
        record["assumptions"] = []
        self.assertEqual(self.errors(record), set())

    def test_cf_5_design_verification_path(self):
        record = copy.deepcopy(self.original)
        record["assumptions"] = [{"topic": "verification-path", "statement": "External check."}]
        self.assertEqual(self.errors(record, design=True), set())
        record["assumptions"][0]["topic"] = "other"
        self.assertEqual(self.errors(record, design=True), {"assumptions"})
        self.assertEqual(self.errors(record, design=False), set())

    def test_cf_6_measurement_field_types(self):
        good = self.measurement()
        for kind in ("inspection", "execution"):
            record = dict(self.original, measurements=[dict(good, kind=kind)])
            self.assertEqual(self.errors(record), set())
        bad = [None, {}, [None]]
        for key in good:
            bad.append([{k: v for k, v in good.items() if k != key}])
        for key, values in {"id": ["", " ", 1], "command": ["", 1], "env": [[], {"A": 1}, {1: "A"}],
                            "exit_code": ["0", 0.5, None], "artifact_revision": [None, 1],
                            "log": [1, []], "note": [None, 1], "kind": [None, "other", 1]}.items():
            bad += [[dict(good, **{key: value})] for value in values]
        self.variants("measurements", bad, "measurements")

    def test_cf_7_duplicate_measurement_ids(self):
        row = self.measurement()
        self.assertEqual(self.errors(dict(self.original, measurements=[row, dict(row, id="n")])), set())
        self.variants("measurements", [[row, copy.deepcopy(row)]], "measurements")

    def test_cf_8_boolean_exit_code(self):
        for value in (True, False):
            self.variants("measurements", [[dict(self.measurement(), exit_code=value)]], "measurements")

    def test_cf_9_artifact_identity_types(self):
        good = {"revision": "rev", "files": [{"path": "a.py", "sha256": "abc"}]}
        for revision in (None, "rev"):
            self.assertEqual(self.errors(dict(self.original, artifact_identity=dict(good, revision=revision))), set())
        bad = [None, [], {"files": []}, dict(good, revision=1), dict(good, files=None), {"revision": "r"}]
        bad += [dict(good, files=[value]) for value in (None, {}, {"path": "a"}, {"sha256": "h"},
                       {"path": 1, "sha256": "h"}, {"path": "a", "sha256": 1})]
        self.variants("artifact_identity", bad, "artifact-identity")

    def test_cf_10_unavailable_source_exact_shape(self):
        good = dict(unavailable=True, source_url="https://example.invalid/source", reason="offline")
        self.assertEqual(self.errors(dict(self.original, unavailable_sources=[good])), set())
        bad = [None, {}, [None], [dict(good, extra="x")]]
        bad += [[{k: v for k, v in good.items() if k != key}] for key in good]
        for key, values in {"unavailable": [False, 1, "true"], "source_url": ["", " ", 1], "reason": ["", " ", 1]}.items():
            bad += [[dict(good, **{key: value})] for value in values]
        self.variants("unavailable_sources", bad, "unavailable-sources")

    def test_cf_11_optional_fields_absent(self):
        for kind, validator in (("audit", "validate_findings.py"), ("design", "validate_judgments.py")):
            record = fixture(kind)
            for key in ("measurements", "artifact_identity", "unavailable_sources"):
                record.pop(key, None)
            result = self.call(kind, validator, record)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
