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


class PlanTests(unittest.TestCase):
    def setUp(self):
            self.record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())

    def assert_plan_error(self):
            self.assertEqual({error["rule"] for error in validate(self.record)}, {"plan"})

    def test_rp_2_plan_render_order_sources_and_served_requirements(self):
            render = renderer.render
            load_catalog = loader.load_catalog
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
            for requirement in self.record["plan"]["requirements"]:
                self.assertIn(f'### {requirement["id"]}: {requirement["statement"]}\n\n{requirement["check"]}\n', requirements)
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

    def test_rp_1_invalid_design_record_cannot_write_plan(self):
            record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
            record["cards"].pop()
            result = self.call("verification-design", "render_plan.py", record, output=True)
            self.assertEqual(result.returncode, 3)
            self.assertFalse(self.output.exists())

    def test_rp_9_unknown_on_rejected_card_surfaces_in_plan(self):
            record = json.loads((ROOT / "skills/fixtures/design-sound/record.json").read_text())
            card = next(c for c in record["cards"] if c["decision"] == "reject")
            card["do_not_use_when"][0]["verdict"] = "unknown"
            card["do_not_use_when"][0]["evidence"] = "The artifact does not establish this exclusion."
            result = self.call("verification-design", "render_plan.py", record, output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(card["do_not_use_when"][0]["condition"], self.output.read_text().split("## Not verified", 1)[1])


class ReleaseTests(unittest.TestCase):
    def run_script(self, kind, name, *args):
            return subprocess.run([sys.executable, str(ROOT / "skills" / ("verification-" + kind) / "scripts" / name), *map(str, args)], capture_output=True, text=True)

    def test_rp_11_resolution_render_preserves_decision_and_position(self):
            render = renderer.render
            load_catalog = loader.load_catalog
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

    def test_rp_3_positive_summaries_and_repeatability(self):
            with tempfile.TemporaryDirectory() as tmp:
                for fixture in sorted((ROOT / "skills/fixtures").glob("design-*/record.json")):
                    kind = "design"
                    validator = "validate_judgments.py"
                    result = self.run_script(kind, validator, fixture)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    counts = json.loads(result.stdout)
                    source = fixture
                    output = Path(tmp) / "result.md"
                    renderer = "render_plan.py"
                    result = self.run_script(kind, renderer, source, "--output", output)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    text = output.read_text()
                    summary = text.split("## Summary\n", 1)[1].split("\n## ", 1)[0]
                    for key in ("apply", "reject", "undecided"):
                        self.assertIn(f'{key}: {counts[key]}', summary.lower())
                    self.assertIn(f'unknown verdicts: {counts["unknown"]}', summary)
                    first = output.read_bytes()
                    self.run_script(kind, renderer, source, "--output", output)
                    self.assertEqual(output.read_bytes(), first)

    def test_rp_13_output_path_refused_when_it_is_the_input_or_inside_the_skill(self):
            with tempfile.TemporaryDirectory() as tmp:
                for kind, folder in (("design", "design-sound"),):
                    skill = ROOT / "skills" / ("verification-" + kind)
                    record = Path(tmp) / (kind + ".json")
                    record.write_text((ROOT / "skills/fixtures" / folder / "record.json").read_text())
                    before = record.read_bytes()
                    renderer = "render_plan.py"
                    scripts = [(renderer, [record])]
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


class RenderContractTests(ScriptCase):
    def setUp(self):
        super().setUp()
        self.value = fixture('design')
        self.catalog, self.meta = loader.load_catalog()

    def text(self):
        self.assertEqual(validate(self.value), [])
        return renderer.render(self.value, self.catalog, self.meta)

    def section(self, title):
        return self.text().split('## ' + title + '\n', 1)[1].split('\n## ', 1)[0]

    def test_rp_1_invalid_record_preserves_destination(self):
        self.value['cards'][0]['reason'] = ''
        self.output.write_bytes(b'Existing plan\n')
        result = self.call('design', 'render_plan.py', self.value, '--output', self.output)
        self.assert_rules(result, ['structure'])
        self.assertEqual(self.output.read_bytes(), b'Existing plan\n')

    def test_rp_3_operator_unknowns(self):
        self.value = json.loads((ROOT / 'skills/fixtures/design-resolved/record.json').read_text())
        summary = self.section('Summary')
        self.assertIn('Apply: 1; reject: 15; undecided: 1; unknown verdicts: 1.', summary)
        self.assertIn('Requirements: 2', summary)
        self.assertIn('Operator decisions:', summary)
        for card in self.value['cards']:
            if card['decision'] == 'undecided':
                title = next(c['title'] for c in self.catalog['cards'] if c['id'] == card['id'])
                unknowns = [c['condition'] for g in ('use_when', 'do_not_use_when') for c in card[g] if c['verdict'] == 'unknown']
                self.assertIn('- ' + title + ': ' + '; '.join(unknowns), summary)

    def test_rp_4_priority_presence_and_order(self):
        self.value['priority'].reverse()
        titles = {c['id']: c['title'] for c in self.catalog['cards']}
        expected = 'Recommended order:\n\n' + '\n'.join(f'{i}. {titles[cid]}' for i,cid in enumerate(self.value['priority'], 1))
        self.assertIn(expected, self.section('Summary'))
        self.value['priority'] = []
        self.assertIn('Recommended order:\n\nNone.', self.section('Summary'))
        self.value.pop('priority')
        self.assertNotIn('Recommended order:', self.text())

    def test_rp_5_workflow_and_points(self):
        self.assertIn('Self-review points:\n\nNone recorded.', self.section('Workflow characterization'))
        self.value['workflow']['self_review_points'] = ['First inspection.', 'Second inspection.']
        text = self.section('Workflow characterization')
        self.assertIn('Self-review points:\n\n- First inspection.\n- Second inspection.', text)
        for key,title in [('generated','Generated'), ('generator','Generator'), ('completion_signal','Completion signal')]:
            self.assertIn(f'{title}: {self.value["workflow"][key]}\n', text)

    def test_rp_6_catalog_order(self):
        self.value['cards'].reverse()
        for title, decision_value in [('Patterns applied','apply'), ('Patterns rejected','reject')]:
            expected_ids = {c['id'] for c in self.value['cards'] if c['decision'] == decision_value}
            expected = ['### ' + c['title'] for c in self.catalog['cards'] if c['id'] in expected_ids]
            self.assertEqual([l for l in self.section(title).splitlines() if l.startswith('### ')], expected)

    def test_rp_7_applied_details(self):
        text = self.section('Patterns applied')
        for card in self.value['cards']:
            if card['decision'] != 'apply': continue
            source = next(c for c in self.catalog['cards'] if c['id'] == card['id'])
            block = text.split('### ' + source['title'] + '\n',1)[1].split('\n### ',1)[0]
            serves = [r['id'] for r in self.value['plan']['requirements'] if card['id'] in r['patterns']]
            self.assertIn('Decision: apply\n\nServes: ' + ', '.join(serves), block)
            for c in card['use_when']:
                line = f'- use_when: {c["condition"]} ({c["verdict"]}). Evidence: {c["evidence"]}'
                if c['verdict'] == 'holds': self.assertIn(line, block)
                else: self.assertNotIn(line, block)
            self.assertIn('Observable signals:\n\n' + '\n'.join('- ' + s for s in source['observable_signal']), block)
            self.assertIn('Determinism move: ' + source['determinism_move'], block)

    def test_rp_8_rejected_conditions_and_labels(self):
        card = next(c for c in self.value['cards'] if c['decision'] == 'reject')
        title = next(c['title'] for c in self.catalog['cards'] if c['id'] == card['id'])
        for exclusion_holds in (True, False):
            for c in card['use_when']: c.update(verdict='does-not-hold', evidence='Use absent.')
            for c in card['do_not_use_when']: c.update(verdict='does-not-hold', evidence='Exclusion absent.')
            if exclusion_holds: card['do_not_use_when'][0].update(verdict='holds', evidence='Exclusion present.')
            block = self.section('Patterns rejected').split('### ' + title + '\n',1)[1].split('\n### ',1)[0]
            expected = ([('do_not_use_when',card['do_not_use_when'][0])] if exclusion_holds else [('use_when',c) for c in card['use_when']])
            self.assertEqual([l for l in block.splitlines() if l.startswith('- ')], [f'- {g}: {c["condition"]} ({c["verdict"]}). Evidence: {c["evidence"]}' for g,c in expected])
        # Renderer labeling is also defined for unknown use conditions in raw input.
        # Such a fallback is unreachable after valid rejection, so exercise render directly.
        card['use_when'][0].update(verdict='unknown', evidence='Not established.')
        block = renderer.render(self.value, self.catalog, self.meta).split('## Patterns rejected',1)[1].split('## Not verified',1)[0]
        c = card['use_when'][0]
        self.assertIn(f'- use_when: {c["condition"]} (unknown). Reason: Not established.', block)

    def test_rp_9_all_unknown_conditions(self):
        card = next(c for c in self.value['cards'] if c['decision'] == 'reject')
        for c in card['do_not_use_when']: c.update(verdict='unknown', evidence='')
        text = self.section('Not verified')
        self.assertIn('Decision: reject', text)
        for c in card['do_not_use_when']:
            self.assertIn('- do_not_use_when: ' + c['condition'].rstrip('.') + '. Reason: Not recorded.', text)

    def test_rp_10_instantiation_all_decisions(self):
        self.value = json.loads((ROOT / 'skills/fixtures/design-resolved/record.json').read_text())
        for decision_value, section in [('apply','Patterns applied'), ('reject','Patterns rejected'), ('undecided','Not verified')]:
            card = next(c for c in self.value['cards'] if c['decision'] == decision_value)
            source = next(c for c in self.catalog['cards'] if c['id'] == card['id'])
            card['instantiation'] = 'Concrete ' + decision_value
            block = self.section(section).split('### ' + source['title'] + '\n',1)[1].split('\n### ',1)[0]
            self.assertIn('Determinism move: ' + source['determinism_move'] + '\n\nInstantiation: Concrete ' + decision_value, block)

    def test_rp_12_unavailable_json(self):
        text = self.section('Not verified')
        for source in self.value['unavailable_sources']:
            self.assertIn(source, [json.loads(block.split('```', 1)[0]) for block in text.split('```json\n')[1:]])
        self.assertNotIn('"unavailable": true', self.text().split('## Not verified',1)[0])

    def test_rp_13_resolved_output_and_repeatability(self):
        self.record.write_text(json.dumps(self.value))
        before = self.record.read_bytes()
        self.assert_refused('design', 'render_plan.py', [self.record], self.record)
        for _ in range(2):
            result = self.run_script('design','render_plan.py',self.record,'--output',self.output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.output.read_bytes(), self.text().encode('utf-8'))
            self.assertEqual(self.record.read_bytes(), before)

    def test_rp_14_stdout_text_envelope(self):
        result = self.call('design', 'render_plan.py', self.value)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), {'text': self.text()})
        self.assertEqual(result.stderr, '')
