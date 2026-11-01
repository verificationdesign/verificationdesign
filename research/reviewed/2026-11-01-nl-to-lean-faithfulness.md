# Beyond Compilation: Evaluating Faithful Natural-Language-to-Lean Statement Formalization

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2606.31002
Evidence grade: C
Grade confidence: medium

## Why It Matters

A checker can validate a generated formal statement without validating its translation of the user's intention. This study measures that gap, then audits the semantic evaluator itself. It therefore bears on two verification boundaries: the boundary between executable validity and intended meaning, and the boundary between an automatic semantic rejection and an actual translation error.

## Method / Evidence

Read: arXiv v4 abstract and full paper (local text extraction, 2026-11-01).

- The main comparison uses eight systems on 227 university-level statements. Acceptance requires Lean compilation and faithfulness grades of at least 9 of 10 from GPT-5.2 and Gemini-2.5-Pro. This is a semantic proxy layered on formal validity, not a formal equivalence proof.
- The tool-augmented agent produces 198/227 compiling outputs (87.2%), while 131/227 (57.7%) satisfy the semantic criterion. Its gap is 29.5 percentage points. Human-majority review confirms 54/67 rejected compiling outputs as genuine mismatches (80.6%); the other 13 are judged faithful. Thus 23.8 points of the gap are human-confirmed translation errors rather than simply automatic rejections.
- Evaluator calibration is measured separately. On the independent Aristotle random audit, one missing output leaves 59 cases: criterion agreement is 54/59 (91.5%), positive precision 44/46 (95.7%), and negative confirmation 10/13 (76.9%). Human agreement is itself imperfect; the paper identifies cases in which Lean contradicts the human majority.
- The later-model extension uses GPT-5.2 alone because Gemini was unavailable. GPT-6 Astra and Claude Opus 5.5 compile 94.3% and 96.0%, with 83.3% accepted for each. The two-stage review classifies 1 of Astra's 25 rejections and 3 of Opus's 29 as translation errors. It attributes the other 50 to the judge (32), defective source statements (11), or both (7). These are review assignments, not a new blinded human audit of both systems.
- Checkability: compilation is independently executable, and BEq supplies Lean-verified implications in both directions for 113/183 accepted-output pairs anchored to human-confirmed statements. The remaining 70 are unresolved by bounded search, not disproved. Neither compilation nor equivalence to a mistaken anchor establishes fidelity to natural-language intent.
- Reproducibility signals: the paper states that code and data are available in the beyond-compilation GitHub repository and describes released human labels, rejection reviews, evaluation scripts, and Lean checks. This review used staged text and did not execute those artifacts.
- Authority signals: the arXiv manuscript lists university affiliations at Riverside, Arizona, and San Diego, without a stated peer-reviewed acceptance. Affiliations tune confidence and do not move the grade.

## Limitations

The benchmark draws from public textbooks and excludes research-level mathematics, leaving possible training exposure and limited domain coverage. Human audits cover the agent and Aristotle. Other rejection assignments depend on a model review whose first stage is also an evaluated generator, including review of its own outputs. Reviewing only rejections does not measure errors among accepted outputs. The later-model extension changes the judging protocol, so its acceptance rates should not be treated as an identical consensus measurement. Human labels and formal anchors also require scrutiny rather than being interchangeable ground truth.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 6 and 7, distinguish formal validity, intended-statement faithfulness, and calibration of the semantic judge. This would narrow "6. Executable Verification Is King" in the synthesis: an executable checker verifies the supplied specification, while semantic rejection still requires external validation. The existence of compiling mistranslations supports a warning now; comparative system rankings and judge reliability require corroboration. Expand-on: yes. Seed topics: formalization specification fidelity audits; semantic judge false rejection calibration; independent Lean translation evaluation.

## Claims Needing Human Review

- Confirm the later-model extension is described as single-judge evidence and model-reviewed error attribution, rather than human-confirmed translation accuracy.
- Review the triage paraphrase's eight-system framing alongside the separately added later models; these are distinct evaluation populations.
- Confirm grade C despite formal certificates and human audits, since the effectiveness claims lack independent replication.
