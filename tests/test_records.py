"""Independent field expectations, byte round trips, and parser failures."""

from dataclasses import fields, replace
from pathlib import Path
import unittest

from research_tools.records import RecordError, parse_scout, parse_triage, render_scout, render_triage

FIXTURES = Path(__file__).parent / "fixtures"


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.scout = (FIXTURES / "scout-sample.md").read_bytes()
        self.triage = (FIXTURES / "triage-sample.md").read_bytes()

    def test_scout_values_and_bytes(self):
        doc = parse_scout(self.scout.decode())
        self.assertEqual((doc.header.title, doc.header.date, doc.header.window),
                         ("Scout 2026-06-09", "2026-06-09", "2026-06-04 to 2026-06-09"))
        self.assertEqual(len(doc.review_queue.entries), 10)
        self.assertEqual(len(doc.deduped_candidates.entries), 10)
        self.assertEqual(len(doc.category_results.categories), 3)
        expected = [
            dict(id="2510.11194", url="https://arxiv.org/abs/2510.11194",
                 title="Aligning Deep Implicit Preferences by Learning to Reason Defensively",
                 authors="Peiming Li, Zhiyuan Hu, Yang Tang, Shiyu Li, Xi Chen", categories="cs.AI",
                 created="2026-06-03", updated="2026-06-04", oai_datestamp="2026-06-04",
                 matched_anchors="LLM, large language model, language model",
                 matched_keywords="process reward model", appeared_in="cs.AI",
                 abstract_excerpt="Personalized alignment is crucial for enabling Large Language Models (LLMs) to engage effectively in user-centric interactions. However, current methods face a dual challenge: they fail to infer users' deep implicit preferences (including unstated goals, semantic context and risk tolerances), and they lack the defensive reasoning required to navigate real-wo..."),
            dict(id="2601.19921", url="https://arxiv.org/abs/2601.19921",
                 title="Demystifying Multi-Agent Debate: The Role of Confidence and Diversity",
                 authors="Xiaochen Zhu, Caiqi Zhang, Yizhou Chi, Tom Stafford, Nigel Collier, Andreas Vlachos",
                 categories="cs.CL, cs.AI", created="2026-06-03", updated="2026-06-04", oai_datestamp="2026-06-04",
                 matched_anchors="LLM, large language model, language model",
                 matched_keywords="multi-agent debate", appeared_in="cs.AI, cs.CL",
                 abstract_excerpt="Multi-agent debate (MAD) is widely used to improve large language model (LLM) performance through test-time scaling, yet recent work shows that vanilla MAD often underperforms simple majority vote despite higher computational cost. Studies show that, under homogeneous agents and uniform belief updates, debate preserves expected correctness and therefore cann..."),
        ]
        queue_values = [
            ("ignore", "The excerpt focuses on a domain application or capability benchmark rather than verification of agent work."),
            ("challenges", "The excerpt says vanilla multi-agent debate can underperform majority vote and isolates confidence and diversity as reliability conditions for debate oversight."),
        ]
        for index, values in enumerate(expected):
            entry = doc.deduped_candidates.entries[index]
            self.assertEqual({f.name: getattr(entry, f.name) for f in fields(entry) if not f.name.startswith("_")}, values)
            queue = doc.review_queue.entries[index]
            self.assertEqual((queue.id, queue.url, queue.title, queue.checked, queue.label, queue.reason),
                             (values["id"], values["url"], values["title"], " ", *queue_values[index]))
            category_entry = doc.category_results.categories[0].records.entries[index]
            self.assertEqual({f.name: getattr(category_entry, f.name) for f in fields(category_entry) if not f.name.startswith("_")},
                             dict(values, appeared_in=None))
        self.assertEqual(render_scout(doc).encode(), self.scout)

    def test_triage_values_and_bytes(self):
        doc = parse_triage(self.triage.decode())
        self.assertEqual((doc.header.title, doc.header.date, doc.header.source_scout, doc.header.reviewer),
                         ("Triage: LLM Judge Scout Batch", "2026-05-31", "research/scouts/scout-2026-05-29.md", "Human + Codex"))
        self.assertEqual(len(doc.candidates), 3)
        expected = [
            ("Reinforcement Learning with Robust Rubric Rewards", "https://arxiv.org/abs/2605.30244", "operational technique", "medium", "promote", [
                "The paper extends RLVR from fully verifiable tasks to partially verifiable vision-language tasks by using rubrics with multiple criteria. It routes criteria either through an extractor plus deterministic verifier or through an LLM judge when the criterion cannot be made deterministic, then masks information to reduce exploitable scoring shortcuts.",
                "- Proposes criterion-level verification rather than only task-level reward.\n- Separates deterministic criteria from non-verifiable criteria handled by an LLM judge.\n- Uses minimal exposure to hide ground truth from extractors and images from judges.\n- Reports better performance than RLVR across 15 benchmarks, plus controlled audits showing fewer exploitable false positives.",
                "This is directly relevant to the current question of pairing executable verification with rubric or judge-based evaluation. It may give a concrete design pattern: split rubric criteria by verifiability, route each criterion to the strongest available checker, and deliberately hide information that would let the checker exploit shortcuts.",
                'Potentially refine Principle 6 or Principle 7 with a note that hybrid verification should be criterion-level, not just task-level. This could add nuance to "executable verification is king" by describing how to handle partially verifiable tasks.',
                "Decision: promote\n\nPromote to reviewed note after reading more than the abstract. This is the strongest candidate from this scout batch.",
            ]),
            ("Personalized Turn-Level User Conversation Satisfaction Benchmark", "https://arxiv.org/abs/2605.29711", "ignore", "medium", "keep-in-scout", [
                "The paper builds a personalized evaluator for turn-level user satisfaction. It combines compact user memories with target-turn context, calibrates scores, and uses the evaluator to compare generic and memory-augmented assistant systems without collecting new human labels for every model.",
                "- Generic response-quality evaluation may miss personalized satisfaction.\n- User memory and score calibration improve agreement with human satisfaction annotations.\n- Replay with fixed state enables controlled comparison of personalized systems.",
                "It is evaluation work, but its target is user satisfaction and personalization rather than verification of agent work. The memory and replay setup is adjacent to controlled evaluation, but not central to the current verification principles.",
                'Probably nothing. At most it is background for "evaluation target must match the property being measured," but that is not a current weak spot in the doc.',
                "Decision: keep-in-scout\n\nDo not promote. Revisit only if the repo later expands into personalized assistant evaluation.",
            ]),
        ]
        headings = ["Abstract Paraphrase", "Key Findings", "Why It Might Matter", "What Would Change In The Doc", "Decision"]
        for candidate, (title, source, label, confidence, decision, bodies) in zip(doc.candidates, expected):
            self.assertEqual((candidate.title, candidate.source, candidate.initial_label, candidate.confidence, candidate.decision),
                             (title, source, label, confidence, decision))
            self.assertEqual([(s.heading, s.body) for s in candidate.sections],
                             [(f"### {heading}\n", f"\n{body}\n\n") for heading, body in zip(headings, bodies)])
        self.assertEqual(render_triage(doc).encode(), self.triage)

    def test_missing_decision_reports_line(self):
        text = self.triage.decode().replace("Decision: promote\n", "", 1)
        with self.assertRaises(RecordError) as caught:
            parse_triage(text)
        self.assertEqual(caught.exception.line, 33)
        self.assertEqual(caught.exception.expected, "decision")

    def test_unknown_top_heading_reports_line(self):
        with self.assertRaises(RecordError) as caught:
            parse_triage(self.triage.decode().replace("## Candidate:", "## Unknown:", 1))
        self.assertEqual(caught.exception.line, 7)
        self.assertIn("supported trailing heading", str(caught.exception))

    def test_missing_entry_id_reports_line(self):
        text = self.scout.decode().replace(" ([arXiv:2510.11194](https://arxiv.org/abs/2510.11194))", "", 1)
        with self.assertRaises(RecordError) as caught:
            parse_scout(text)
        self.assertEqual(caught.exception.line, 14)
        self.assertIn("arXiv id", str(caught.exception))

    def test_preserves_extensions_and_trailing_sections(self):
        extra = "### Reader Notes\n\nKeep  spacing.\nWrapped\nprose.\n\n"
        text = self.triage.decode().replace("### Decision\n", extra + "### Decision\n", 1)
        text += "## Run Complete\n\nNo normalization.\n"
        doc = parse_triage(text)
        self.assertEqual(doc.candidates[0].sections[-2].render(), extra)
        self.assertEqual(doc.trailing_sections[0].body, "\nNo normalization.\n")
        self.assertEqual(render_triage(doc), text)
        text = self.scout.decode() + "## Run Complete\n\nDone.\n\n## Extra Notes\nKeep me.\n"
        doc = parse_scout(text)
        self.assertEqual([(s.heading, s.body) for s in doc.trailing_sections],
                         [("## Run Complete\n", "\nDone.\n\n"), ("## Extra Notes\n", "Keep me.\n")])
        self.assertEqual(render_scout(doc), text)

    def test_scout_absence_wrapping_and_cap(self):
        text = self.scout.decode().replace("  - Matched anchors: LLM, large language model, language model\n", "", 1)
        text = text.replace("  - Updated: 2026-06-04", "  - Updated: (unknown)", 1)
        text = text.replace("real-wo...", "real-wo...\n    Continued excerpt.", 1)
        text = text.replace("### Category: `cs.AI` (set `cs:cs:AI`)",
                            "### Category: `cs.AI` (set `cs:cs:AI`) (capped at --max-per-category 10; later matches in the window were not read)", 1)
        doc = parse_scout(text)
        self.assertEqual(doc.deduped_candidates.entries[0].updated, "(unknown)")
        self.assertIsNone(doc.deduped_candidates.entries[0].matched_anchors)
        self.assertTrue(doc.deduped_candidates.entries[0].abstract_excerpt.endswith("\n    Continued excerpt."))
        self.assertEqual(doc.category_results.categories[0].capped_at, 10)
        self.assertEqual(render_scout(doc), text)

    def test_render_uses_values_and_section_bodies(self):
        doc = parse_triage(self.triage.decode())
        first = doc.candidates[0]
        section = replace(first.sections[0], body="\nRevised prose.\n\n")
        decision = replace(first.sections[-1], decision="ignore")
        first = replace(first, title="Revised title", sections=(section, *first.sections[1:-1], decision))
        changed = render_triage(replace(doc, candidates=(first, *doc.candidates[1:])))
        parsed = parse_triage(changed)
        self.assertEqual(parsed.candidates[0].title, "Revised title")
        self.assertEqual(parsed.candidates[0].sections[0].body, "\nRevised prose.\n\n")
        self.assertEqual(parsed.candidates[0].decision, "ignore")
        doc = parse_scout(self.scout.decode())
        entry = replace(doc.deduped_candidates.entries[0], title="Revised title", authors="One author")
        section = replace(doc.deduped_candidates, entries=(entry, *doc.deduped_candidates.entries[1:]))
        changed = parse_scout(render_scout(replace(doc, deduped_candidates=section)))
        self.assertEqual(changed.deduped_candidates.entries[0].title, "Revised title")
        self.assertEqual(changed.deduped_candidates.entries[0].authors, "One author")
