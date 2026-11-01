# The Anatomy of a Blind Spot: What an LLM Judge Must Be Shown, and How Much

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.15938
Evidence grade: C
Grade confidence: medium

## Why It Matters

This paper changes what judges can inspect before comparing judge capability. Its strongest relevance to Principles 1 and 7 is that an external model is still an inadequate verifier when denied the source or requirements that define correctness. It also tests what happens when a system acts on defective feedback, with outcomes checked separately from the feedback judge.

## Method / Evidence

Read: arXiv abstract and full paper (local text extraction, 2026-11-01; version stamp not present in extraction).

- Design: seven public benchmarks span grounding, translation, summarization, instruction following, and arithmetic. The principal judge is Gemini 2.5 Flash, with Claude Haiku 4.5 replication and a Claude Opus 4.8 capability comparison. Blind and informed arms hold judging prompts fixed except for evidence availability, with pooling rules specified by output format.
- Headline evidence-channel result: on 1,100 human-labeled LLM-AggreFact claims, blind balanced accuracies range from 0.565 to 0.587 across the three judges; document-informed accuracies range from 0.775 to 0.795. This comparison uses corpus labels without the paper's defect matcher. Capability does not compensate for absent evidence within this tested panel.
- Headline closed-loop result: on 1,080 IFEval responses covering 1,664 constraints, blind feedback changes constraint pass rate by -0.145, with interval -0.168 to -0.123, breaking 331 constraints and fixing 90. A no-report revision control gains +0.025. The blind arm lacks the instruction itself; it is stricter than a typical judge that sees a user request. The informed judge's +0.038 does not establish superiority over no-report revision across the paper's comparisons.
- Reference-summary result: on 310 FRANK summaries, source-only balanced accuracy is 0.769 and source-plus-reference accuracy is 0.618, with precision falling from 0.739 to 0.579. Recall rises from 0.844 to 0.931 while false positives rise from 31% to 70%. These figures use the generous matching route with the principal judge. They measure added false accusations, not simple failure to detect errors.
- Scope counterexample: on 500 HaluEval QA pairs, reference-only balanced accuracy is 0.919, against 0.852 with source knowledge and 0.645 with neither. Adding the reference to the knowledge improves accuracy by 0.051. This exploratory single-answer setting prevents a general warning against reference answers.
- Theory shortfall: of 83 internally committed clauses, 81 run, 32 meet their bars, and 50 go in the predicted direction. The paper reports failed quantitative predictions rather than validating the regulatory theory wholesale.
- Checkability: evidence ablations and checker-scored repair loops can be independently rerun. IFEval constraints and GSM8K answer keys avoid using the feedback judge to certify its repairs. This mechanism does not certify matcher decisions, human factuality labels, or the authors' proposed explanation of reference dominance.
- Reproducibility signals: the underlying corpora are public; judge prompts, the prediction ledger, verification log, and per-run results are available from the authors on request. Private commits have no third-party timestamps, so their pre-commitment status is not independently verifiable as public preregistration. No artifact was executed for this review.
- Authority signals: this is an arXiv preprint listing Hosho as the organizational affiliation and supplying no peer-review acceptance claim. Organizational affiliation tunes confidence and does not move the evidence grade.

## Limitations

Some defect scores depend on a model-based matcher with no human audit, and matching routes can reverse a contrast. HaluEval loop scoring sometimes uses entailment, so automatic there does not mean purely programmatic. The reference results cover a single summarization corpus and a single QA corpus; repeat votes are not independent corroboration. Commercial judge coverage is limited, the second-family loop replication is exploratory, and intervals are descriptive. The shorter-evidence experiment retains recall but fails its committed false-positive bar, so it does not establish that aggressive evidence reduction is safe.

## Suggested Update

Disposition: fold-a-narrow-warning. For Principles 1 and 7, recommend auditing a judge's evidence channel and scoring feedback-induced revisions with an independent outcome check. The FRANK result supports and narrows the held note research/reviewed/2026-06-19-summarization-faithfulness-checks.md: it corroborates unreliable summarization fidelity gates and adds that an acceptable reference can interfere with source-grounded judging. It does not contradict that note's scoped detector warning or show that references harm single-answer verification. It would also corroborate "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." Hold general effectiveness and theory claims pending independent work. Expand-on: yes. Seed topics: reference interference in summarization judges; evidence-channel ablations for feedback loops; independent replication of source-grounded judging.

## Claims Needing Human Review

- Whether grade C and medium confidence adequately distinguish matcher-free evidence from model-scored contrasts.
- Whether the FRANK experiment meets the fold bar for a narrow warning despite the reference mechanism remaining an interpretation.
- Whether this explicitly scoped support for the held summarization note captures triage's expand-on challenge without implying that all reference use is harmful.
