# Rubrics Carry the Standard: Shapley Attribution for Checklist-Based LLM Judges

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.24971
Evidence grade: C
Grade confidence: medium

## Why It Matters

Checklist content and its aggregation rule are part of the measurement instrument. Changing them can change what counts as success even when the outputs and judging model stay fixed. The paper makes rubric revision observable through per-check catches, false failures, and provenance, while showing that a model's own review can discard criteria that external labels made useful.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- The controlled Recon-72 strictness population contains 24 correct and 48 flawed reports. Hand checks pass 95.8% of correct reports as a checklist, 97.9% as a paragraph, and 95.8% on the ordinal rendering. The ranked generated checks pass 4.2%, 4.2%, and 8.3%, while both rubric sets catch every planted flaw. This is a content comparison on authored reports, not a universal model strictness estimate.
- Recon-108 revision experiments contain 36 correct and 72 flawed reports, including unanticipated omissions. Across revision chains, 186 deleted checks include 78 with a unique catch and only 2 carrying any false-fail blame. Deletion therefore often removes nonredundant coverage rather than eliminating observed false failures.
- Public-data tests use 146 SummEdits summaries and 160 RAGTruth responses. On the RAGTruth sample, free-form grading passes 80.6% of faithful responses and catches 88.1% of hallucinated ones; ten checks yield 41.2% passed and 95.0% caught. Correct acceptance and flaw detection must be reported separately.
- The combined Shapley and provenance gate keeps unplanned caught at 100% on the label-taught Recon chains and correct passed at 91.7 to 95.8% on hand-rubric chains. The exception is Sonnet's label-taught chain: correct passed is 58.3% against 75.0% initially. A rewrite was unmatched to its frozen predecessor and entered as an addition, exposing a concrete gate failure.
- Checkability: under all-must-pass aggregation, each failed output's attribution is divided equally among its failing checks. Fixed per-check answers and external labels allow deterministic recomputation of catch credit, false-fail blame, and unique catches. This accounting does not verify labels, requirement legitimacy, semantic check matching, or invariance of answers when neighboring checks change.
- Reproducibility signals: the paper supplies attribution formulas, gate definitions, prompts, examples, and stored-answer replay descriptions. The paper text read for this review does not state whether code or data are released. This review did not execute a replay or inspect external artifacts.
- Authority signals: the manuscript explicitly says Microsoft and Preprint and lists industry-affiliated authors. These facts tune confidence and do not move the grade; internal dataset replication is not independent corroboration.

## Limitations

Recon reports and labels are synthetic and author controlled. SummEdits and RAGTruth broaden coverage to human-labeled consistency and faithfulness tasks, not independent agentic evaluations. All judges, rubric authors, and revisers are Claude models, so robustness across judges remains within one family. Small correct-report and rare-omission populations limit interpretation of small differences. Gate evaluation primarily replays stored answers, assuming answers do not depend on neighboring checks; spot re-grades agreed within 4.2 points. Similarity-based matching and leave-one-out labels leave demonstrated blind spots for rewritten checks and rare flaws.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 1 and 5, preserve externally supported rubric requirements and test revisions against separate correct-acceptance and flaw-detection signals. This corroborates the concern organized under "5. Explicit Criteria" in the synthesis while narrowing any assumption that explicitness alone validates a rubric. The checkable attribution mechanism supports an executable diagnostic; effectiveness of the combined gate remains held for independent corroboration. Expand-on: yes. Seed topics: cross-family rubric revision replication; provenance preserving checklist gates; rare flaw coverage attribution.

## Claims Needing Human Review

- Confirm the selected Recon headline fairly represents a content intervention rather than an isolated change in rubric length or aggregation.
- Review whether the combined gate exception should receive more emphasis than the triage's general statement that gating limits drift.
- Confirm grade C and the distinction between within-paper public-dataset replication and independent corroboration.
