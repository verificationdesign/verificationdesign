# Agreement Without Alignment: Label-Free Rubric Clarification Increases LLM-Judge Consensus but Not Agreement with Humans

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.13303
Evidence grade: C
Grade confidence: medium

## Why It Matters

The paper separates making evaluation criteria less contentious for judges from making their judgments better match people. This bears on Principles 5 and 7 because consensus can be an internal optimization target that never validates the criterion being optimized. A held-out human comparison and a matched editing control make the distinction observable rather than assuming that clearer criteria must improve validity.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- Procedure: an editor decomposes rubrics, ranks clauses by development-set judge disagreement, and rewrites selected clauses without human labels. A random-clause control edits an equal number of unselected clauses using the same editor and example rule. Development and evaluation splits are separated by article or conversation cluster; evaluation labels are extracted after the manifest is sealed.
- Population: five judges from three providers evaluate six rubric conditions on SummEval, HealthBench meta-evaluation, and USR Topical-Chat. The panel contains Claude Opus 5.5, Claude Sonnet 5.5, Claude Haiku 4.5, GPT-6 Luna, and Gemini 3.5 Flash-Lite. The paper reports 129,770 judge requests excluding retries. Planned evaluation units are 1,280, 799, and 1,728 item-dimension pairs respectively; valid human-comparison populations vary with parsing and label availability.
- Headline SummEval result: clarification increases inter-judge Krippendorff's alpha by 0.069 over the original rubric, with 95% CI 0.046 to 0.092, and by 0.074 over the matched control. Agreement with expert ratings shows no detectable change: Kendall tau difference -0.007, with 95% CI -0.037 to 0.021. These are separately measured outcomes on the SummEval evaluation split.
- Narrowing result: neither HealthBench nor USR meets the preregistered criteria for increased inter-judge agreement or improved human agreement. USR's alpha increase is 0.027, below the 0.05 effect threshold, with Holm-adjusted p = 0.070. HealthBench's human-agreement difference is -0.023, with Holm-adjusted p = 0.155; the paper does not report it as a significant decrease. Failure to detect improvement is not an equivalence result.
- Transfer-to-code result: no sub-criterion among the 75 decomposed criteria is mapped to the available checkers. The code-transfer stage is therefore unexercised, and its proposed agreement threshold is not tested. The procedure edits 23 clauses in each editing condition; this evaluates clarification rather than successful replacement of semantic judging by code.
- Checkability: cluster splitting, disagreement ranking, bounded selection, fixed-control sampling, and metric recomputation are executable given frozen artifacts. They verify the selection and evaluation procedure, not whether an editor preserved every intended criterion or whether human labels capture the right standard. Model editing remains semantic judgment.
- Reproducibility signals: the abstract promises release of code, frozen rubrics, item identifiers, and judge scores; the ethics section describes artifacts to be released. This is a release commitment rather than confirmation that the review obtained artifacts. The paper records version-controlled self-registration and a sealed manifest, not registration in an external registry.
- Authority signals: the source is an arXiv preprint listing CEO Business School as the institutional affiliation, without a peer-review acceptance statement in the text. These authority facts tune confidence and do not move the evidence grade.

## Limitations

The panel and editor share a model family, while the other providers are represented by smaller judges. Provider, size, and reasoning settings are confounded. HealthBench edits affect a limited fraction of evaluation items, and existing human labels are noisy. The study covers English benchmarks and a single editing pass. Protocol changes before evaluation include model and output-setting changes and a relaxed pre-flight criterion. Intervals are unadjusted while p-values are adjusted, so an interval excluding zero alone is insufficient for the paper's significance claims. This review did not reproduce any run or inspect released scores.

## Suggested Update

Disposition: fold-a-narrow-warning. For Principles 5 and 7, this would narrow "Explicit rubrics remain sensitive to how criteria are presented and executed." A rubric repair should report external-label agreement separately from internal panel consensus and compare targeting with an editing control. The SummEval result warrants that scoped warning; effectiveness across tasks and benefits from transfer to code remain held for corroboration. No canonical fold is performed. Expand-on: yes. Seed topics: rubric repair and human alignment; matched controls for judge clarification; deterministic criterion transfer evaluation.

## Claims Needing Human Review

- Whether grade C with medium confidence is appropriate despite the controlled design, given pending artifacts and no independent reproduction.
- Whether the warning should emphasize absence of detectable alignment gain rather than the title's stronger apparent claim of no agreement benefit.
- Whether triage's narrowing label sufficiently distinguishes the untested code-transfer stage from the tested clarification procedure.
