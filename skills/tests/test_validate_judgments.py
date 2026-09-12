"""Inventory-mapped design script contract tests."""
import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from support import ROOT, DESIGN, ScriptCase, fixture, module
validator = module("validate_judgments", "design")
validate = validator.validate
decision = validator.decision
renderer = module("render_plan", "design")
loader = module("load_catalog", "design")


class DecisionTests(unittest.TestCase):
    def test_vj_15_all_nine_decision_combinations(self):
            expected = {
                ("holds", "holds"): "reject", ("holds", "does-not-hold"): "apply", ("holds", "unknown"): "undecided",
                ("does-not-hold", "holds"): "reject", ("does-not-hold", "does-not-hold"): "reject", ("does-not-hold", "unknown"): "reject",
                ("unknown", "holds"): "reject", ("unknown", "does-not-hold"): "undecided", ("unknown", "unknown"): "undecided",
            }
            for pair in itertools.product(("holds", "does-not-hold", "unknown"), repeat=2):
                with self.subTest(pair=pair):
                    self.assertEqual(decision([pair[0]], [pair[1]]), expected[pair])

    def test_vj_1_malformed_records_fail_validation_without_crash(self):
            catalog, _ = loader.load_catalog()
            for value in (None, [], "record", 1):
                with self.subTest(value=value):
                    self.assertEqual({e["rule"] for e in validate(value, catalog)}, {"structure"})

    def test_vj_10_duplicate_card_rejected(self):
            record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
            record["cards"].append(copy.deepcopy(record["cards"][0]))
            self.assertEqual({error["rule"] for error in validate(record)}, {"coverage"})

    def test_vj_16_unknown_exclusion_cannot_apply(self):
            record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
            card = next(c for c in record["cards"] if c["decision"] == "apply")
            card["do_not_use_when"][0]["verdict"] = "unknown"
            self.assertEqual({error["rule"] for error in validate(record)}, {"decision-undecided"})


class PlanTests(unittest.TestCase):
    def setUp(self):
            self.record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())

    def assert_plan_error(self):
            self.assertEqual({error["rule"] for error in validate(self.record)}, {"plan"})

    def test_vj_3_missing_or_non_object_plan(self):
            self.record.pop("plan")
            self.assert_plan_error()
            for value in (None, [], "design"):
                self.record["plan"] = value
                self.assert_plan_error()

    def test_vj_3_plan_keys(self):
            original = copy.deepcopy(self.record["plan"])
            for key in ("design", "requirements"):
                self.record["plan"] = copy.deepcopy(original)
                self.record["plan"].pop(key)
                self.assert_plan_error()
            self.record["plan"] = dict(original, extra=True)
            self.assert_plan_error()

    def test_vj_4_plan_design_nonempty_string(self):
            for value in (None, [], 1, "", " "):
                self.record["plan"]["design"] = value
                self.assert_plan_error()

    def test_vj_4_plan_source_nonempty_string_when_present(self):
            for value in (None, [], 1, "", " "):
                self.record["plan"]["source"] = value
                self.assert_plan_error()
            self.record["plan"].pop("source")
            self.assertEqual(validate(self.record), [])

    def test_vj_5_requirements_nonempty_list(self):
            for value in (None, {}, "V1", []):
                self.record["plan"]["requirements"] = value
                self.assert_plan_error()

    def test_vj_5_requirement_object_and_exact_keys(self):
            original = copy.deepcopy(self.record["plan"]["requirements"][0])
            variants = [None, [], {}, dict(original, extra=True)]
            variants += [{k: v for k, v in original.items() if k != key} for key in original]
            for value in variants:
                self.record["plan"]["requirements"][0] = value
                self.assert_plan_error()

    def test_vj_6_requirement_ids_contiguous_in_order(self):
            for value in ("V3", "V1", "v2", 2, None, []):
                self.record["plan"]["requirements"][1]["id"] = value
                self.assert_plan_error()
            self.record["plan"]["requirements"][1]["id"] = "V2"
            self.record["plan"]["requirements"].reverse()
            self.assert_plan_error()

    def test_vj_7_requirement_statement_nonempty_string(self):
            for value in (None, [], 1, "", " "):
                self.record["plan"]["requirements"][0]["statement"] = value
                self.assert_plan_error()

    def test_vj_7_requirement_check_nonempty_string(self):
            for value in (None, [], 1, "", " "):
                self.record["plan"]["requirements"][0]["check"] = value
                self.assert_plan_error()

    def test_vj_8_patterns_must_be_list(self):
            for value in (None, {}, "verification/comparator"):
                self.record["plan"]["requirements"][1]["patterns"] = value
                self.assert_plan_error()

    def test_vj_8_patterns_name_only_applied_cards(self):
            for value in (None, [], {}, "missing/card", "context-and-state/constitution"):
                self.record["plan"]["requirements"][1]["patterns"] = [value]
                self.assert_plan_error()
            self.record = json.loads((ROOT / "skills/fixtures/design-resolved/record.json").read_text())
            self.record["plan"]["requirements"][1]["patterns"] = ["verification/executable-analog"]
            self.assert_plan_error()

    def test_vj_8_patterns_no_duplicates_within_requirement(self):
            patterns = self.record["plan"]["requirements"][0]["patterns"]
            patterns.append(patterns[0])
            self.assert_plan_error()

    def test_vj_9_every_applied_card_serves_requirement(self):
            self.record["plan"]["requirements"][0]["patterns"].pop()
            self.assert_plan_error()

    def test_vj_9_empty_patterns_and_card_serving_multiple_requirements(self):
            self.assertEqual(validate(self.record), [])
            self.record["plan"]["requirements"][1]["patterns"] = ["verification/comparator"]
            self.assertEqual(validate(self.record), [])


class ReleaseTests(unittest.TestCase):
    def run_script(self, kind, name, *args):
            return subprocess.run([sys.executable, str(ROOT / "skills" / ("verification-" + kind) / "scripts" / name), *map(str, args)], capture_output=True, text=True)

    def test_vj_19_resolution_positive_and_four_negative_fixtures(self):
            folder = ROOT / "skills/fixtures/design-resolved"
            record = json.loads((folder / "record.json").read_text())
            self.assertEqual(validate(record), [])
            for name in ("applied", "bad-date", "unknown-measurement", "extra-key"):
                with self.subTest(name=name):
                    path = folder / f"negative-resolution-{name}.json"
                    result = self.run_script("design", "validate_judgments.py", path)
                    self.assertEqual(result.returncode, 3, result.stderr)
                    self.assertEqual({e["rule"] for e in json.loads(result.stdout)}, {"resolution"})

    def test_vj_20_resolution_types_calendar_dates_and_absent_measurements(self):
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


class JudgmentContractTests(ScriptCase):
    def rules(self, record, expected):
        errors = validate(record)
        self.assertEqual({e['rule'] for e in errors}, set(expected), errors)
        for error in errors:
            self.assertEqual(set(error), {'card', 'rule', 'message'})
            self.assertIsInstance(error['message'], str)
            self.assertTrue(error['message'])
        return errors

    def test_vj_1_isolated_record_fields(self):
        self.rules(fixture('design'), [])
        for value in (None, [], 'record', 1):
            self.rules(value, ['structure'])
        for key in ('artifact', 'scope', 'corpus_revision'):
            for value in (None, '', ' ', [], 1):
                record = fixture('design')
                record[key] = value
                self.rules(record, ['structure'])
            record = fixture('design')
            record.pop(key)
            self.rules(record, ['structure'])
        for key, value in (('scope', 'first\nsecond'), ('corpus_revision', '0' * 40)):
            record = fixture('design')
            record[key] = value
            self.rules(record, ['structure'])

    def test_vj_2_workflow_fields(self):
        for key in ('generated', 'generator', 'completion_signal', 'self_review_points'):
            for value in (None, '', ' ', {}, 1):
                record = fixture('design')
                record['workflow'][key] = value
                self.rules(record, ['structure'])
            record = fixture('design')
            record['workflow'].pop(key)
            self.rules(record, ['structure'])
        for value in ([''], [' '], [1], [None]):
            record = fixture('design')
            record['workflow']['self_review_points'] = value
            self.rules(record, ['structure'])
        for value in (None, [], 'workflow'):
            record = fixture('design')
            record['workflow'] = value
            self.rules(record, ['structure'])
        record = fixture('design')
        record['workflow']['self_review_points'] = ['Review the generated result.']
        self.rules(record, [])

    def test_vj_10_exact_catalog_coverage(self):
        for mode in ('missing', 'duplicate', 'unknown'):
            record = fixture('design')
            card = next(c for c in record['cards'] if c['decision'] == 'reject')
            if mode == 'missing': record['cards'].remove(card)
            elif mode == 'duplicate': record['cards'].append(copy.deepcopy(card))
            else: card['id'] = 'unknown/card'
            self.rules(record, ['coverage'])

    def test_vj_11_verbatim_order_both_groups(self):
        for group in ('use_when', 'do_not_use_when'):
            for mode in ('reverse', 'missing', 'changed'):
                record = fixture('design')
                card = next(c for c in record['cards'] if len(c[group]) > 1)
                if mode == 'reverse': card[group].reverse()
                elif mode == 'missing': card[group].pop()
                else: card[group][0]['condition'] += ' changed'
                self.rules(record, ['conditions'])

    def test_vj_12_card_structure(self):
        for value in (None, {}, 'cards'):
            record = fixture('design')
            record['cards'] = value
            # Applied requirements would be a separate plan violation.
            for req in record['plan']['requirements']: req['patterns'] = []
            record.pop('priority', None)
            self.rules(record, ['structure'])
        for key, values in (('id', [None, '', ' ', 1, []]), ('reason', [None, '', ' ', 1]),
                            ('use_when', [None, {}, [None]]), ('do_not_use_when', [None, {}, [1]])):
            for value in values:
                record = fixture('design')
                card = next(c for c in record['cards'] if c['decision'] == 'reject')
                card[key] = value
                self.rules(record, ['structure'])
        record = fixture('design')
        index = next(i for i,c in enumerate(record['cards']) if c['decision'] == 'reject')
        for value in (None, [], 'card'):
            changed = copy.deepcopy(record)
            changed['cards'][index] = value
            self.rules(changed, ['structure'])

    def test_vj_13_verdict_and_evidence(self):
        for group in ('use_when', 'do_not_use_when'):
            for key, values in (('verdict', [None, [], '', 'invalid']), ('evidence', [None, [], '', ' '])):
                for value in values:
                    record = fixture('design')
                    record['cards'][0][group][0][key] = value
                    self.rules(record, ['verdicts'])
            record = fixture('design')
            card = next(c for c in record['cards'] if c['decision'] == 'reject')
            card[group][0].update(verdict='unknown', evidence='')
            card['decision'] = decision([c['verdict'] for c in card['use_when']], [c['verdict'] for c in card['do_not_use_when']])
            self.rules(record, [])

    def mismatch(self, use, exclude, expected):
        record = fixture('design')
        card = next(c for c in record['cards'] if c['decision'] == 'reject')
        for c in card['use_when']: c.update(verdict=use, evidence='Observed use.')
        for c in card['do_not_use_when']: c.update(verdict=exclude, evidence='Observed exclusion.')
        card['decision'] = 'undecided' if expected != 'undecided' else 'reject'
        errors = self.rules(record, ['decision-' + expected])
        self.assertEqual({e['card'] for e in errors}, {card['id']})

    def test_vj_14_apply_mismatch(self):
        self.mismatch('holds', 'does-not-hold', 'apply')

    def test_vj_15_reject_mismatch(self):
        self.mismatch('holds', 'holds', 'reject')
        self.mismatch('does-not-hold', 'unknown', 'reject')

    def test_vj_16_undecided_mismatch(self):
        self.mismatch('holds', 'unknown', 'undecided')
        self.mismatch('unknown', 'does-not-hold', 'undecided')

    def test_vj_17_priority(self):
        record = fixture('design')
        applied = next(c['id'] for c in record['cards'] if c['decision'] == 'apply')
        rejected = next(c['id'] for c in record['cards'] if c['decision'] == 'reject')
        for value in (None, {}, applied, [applied, applied], [rejected], [None], [[]]):
            changed = copy.deepcopy(record)
            changed['priority'] = value
            self.rules(changed, ['priority'])
        for value in ([], [applied]):
            record['priority'] = value
            self.rules(record, [])
        record.pop('priority')
        self.rules(record, [])

    def test_vj_18_instantiation(self):
        for value in (None, [], {}, 1):
            record = fixture('design')
            record['cards'][0]['instantiation'] = value
            self.rules(record, ['instantiation'])
        for value in ('', 'Specific implementation.'):
            record['cards'][0]['instantiation'] = value
            self.rules(record, [])

    def test_vj_19_resolution_exact_keys(self):
        original = json.loads((ROOT / 'skills/fixtures/design-resolved/record.json').read_text())
        for key in ('date', 'observation', 'evidence', 'measurement'):
            record = copy.deepcopy(original)
            next(c for c in record['cards'] if 'resolution' in c)['resolution'].pop(key)
            self.rules(record, ['resolution'])

    def test_vj_21_measurement_reference(self):
        record = json.loads((ROOT / 'skills/fixtures/design-resolved/record.json').read_text())
        card = next(c for c in record['cards'] if 'resolution' in c)
        self.rules(record, [])
        card['resolution']['measurement'] = 'absent'
        self.rules(record, ['resolution'])
        card['resolution']['measurement'] = None
        self.rules(record, [])

    def test_vj_22_diagnostics_and_stage_boundaries(self):
        record = fixture('design')
        record['cards'][0]['reason'] = ''
        result = self.call('design', 'validate_judgments.py', record)
        self.assert_rules(result, ['structure'])
        self.assertEqual(json.loads(result.stdout), [{'card': record['cards'][0]['id'], 'rule': 'structure', 'message': 'reason must be non-empty'}])
        self.assertEqual(result.stderr, 'judgment validation failed\n')
        # Each malformed record violates one rule; spies prove later decision work stops.
        changes = [('structure', lambda c: c.update(reason='')),
                   ('coverage', lambda c: c.update(id='absent/card')),
                   ('conditions', lambda c: c['use_when'][0].update(condition='changed')),
                   ('verdicts', lambda c: c['use_when'][0].update(verdict='bad'))]
        for rule, change in changes:
            record = fixture('design')
            card = next(c for c in record['cards'] if c['decision'] == 'reject')
            change(card)
            with patch.object(validator, 'decision', wraps=decision) as later:
                self.rules(record, [rule])
                later.assert_not_called()

    def test_vj_23_cli_complete_counts(self):
        record = json.loads((ROOT / 'skills/fixtures/design-resolved/record.json').read_text())
        result = self.call('design', 'validate_judgments.py', record)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), {'valid': True, 'cards': 17, 'apply': 1, 'reject': 15, 'undecided': 1, 'unknown': 1})
        self.assertEqual(result.stderr, '')


    def test_vj_22_each_later_stage_is_not_entered(self):
        class Probe(dict):
            def __init__(self, value):
                super().__init__(value)
                self.reads = []
            def __getitem__(self, key):
                self.reads.append(key)
                return super().__getitem__(key)
            def get(self, key, default=None):
                self.reads.append(key)
                return super().get(key, default)
        catalog, meta = loader.load_catalog()
        record = fixture('design')
        record['cards'][0]['reason'] = ''
        probed_catalog = Probe(catalog)
        self.assertEqual({e['rule'] for e in validate(record, probed_catalog, meta)}, {'structure'})
        self.assertNotIn('cards', probed_catalog.reads)
        record = fixture('design')
        rejected = next(c for c in record['cards'] if c['decision'] == 'reject')
        rejected['id'] = 'unknown/card'
        probe = Probe(record['cards'][0]['use_when'][0])
        record['cards'][0]['use_when'][0] = probe
        self.rules(record, ['coverage'])
        self.assertNotIn('condition', probe.reads)
        record = fixture('design')
        probe = Probe(record['cards'][0]['use_when'][0])
        probe['condition'] = 'changed'
        record['cards'][0]['use_when'][0] = probe
        self.rules(record, ['conditions'])
        self.assertNotIn('verdict', probe.reads)
        probe['condition'] = catalog['cards'][0]['use_when'][0]
        probe['verdict'] = 'invalid'
        with patch.object(validator, 'decision', wraps=decision) as later:
            self.rules(record, ['verdicts'])
            later.assert_not_called()
