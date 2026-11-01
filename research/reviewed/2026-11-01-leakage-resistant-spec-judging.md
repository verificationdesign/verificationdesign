# Leakage-Resistant Evaluation of AI-Generated Database Specifications in Specification-Driven Migration

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.12778
Evidence grade: C
Grade confidence: high

## Why It Matters

A judge benchmark can exclude ground-truth leakage while retaining shortcuts that make its binary score difficult to interpret. This paper separates those problems in specification evaluation. Its useful methodological contribution is to test the inference boundary, compare judges with trivial baselines, and measure the category and evidence attached to a finding separately from whether any issue is reported.

## Method / Evidence

Read: arXiv abstract and full paper (local text extraction, 2026-11-01; version stamp not present in extraction).

- Population and protocol: LRFB contains 494 synthetic Oracle PL/SQL source-specification pairs across 19 metrics. Each metric has 26 records split into development and held-out subsets of 13, each containing three clean and ten defective specifications. Source-sharing records stay in the same partition. GPT-4o, DeepSeek V4 Pro, and Claude Sonnet 4.5 receive the same templates, schema constraints, temperature 0, and three runs per record; valid responses are aggregated by majority vote.
- Primary comparison: on 247 held-out records, containing 190 violated and 57 clean cases, balanced accuracy is 0.87 for GPT-4o, 0.89 for DeepSeek V4 Pro, and 0.81 for Claude Sonnet 4.5. A per-metric specification-length threshold reaches 0.88; the always-issue baseline reaches 0.50 balanced accuracy. Judge-versus-length paired McNemar tests yield p=0.73, p=0.38, and p=0.74 respectively. Failure to separate these methods is not proof of equivalence or proof that every judge used length.
- Typed findings: the labelled category occurs among findings in 159/190, 168/190, and 174/190 held-out violated records respectively. Evidence overlap is 130/140, 130/140, and 129/140 among applicable held-out records. Category agreement and span overlap provide additional measured information, but do not independently establish source-semantic reasoning. The paper does not show that requiring typed, evidence-linked findings improves binary accuracy: there is no matched ablation isolating that requirement.
- Canary control, separately: the test suite inserts a unique sentinel into every ground-truth cell and asserts that none appears in model requests, inference logs, or model-output tables. The paper reports this as an executable boundary check, not as an accuracy estimate or a reported population-level leakage rate.
- Label-permutation control, separately: rewriting labels leaves model requests and inference outputs byte-identical. This checks independence of the inference path from those label fields; it does not remove correlations between labels and permitted inference inputs. The original identifiers encoded labels, so identifiers were replaced with input hashes and withheld from judges.
- Checkability: sentinel exclusion, byte identity under label permutation, quotation matching, schema validation, and the length comparator can be reproduced independently. These mechanisms verify a declared data boundary and surface properties, not label correctness, completeness of defect annotation, or the causal contribution of evidence-linked output to accuracy.
- Reproducibility signals: the paper describes a test suite, inference framework, and evaluator prototypes. The paper text read for this review does not state whether code or data are released. No implementation was executed.
- Authority signals: the arXiv paper lists EPAM Systems industry affiliations; the text does not state a peer-reviewed acceptance. These facts tune confidence only and do not move the evidence grade or substitute for independent validation.

## Limitations

The silver-standard labels and authored specifications were not exhaustively validated by independent database experts. Each metric has only 13 held-out records, including three clean cases, and the pooled analysis does not explicitly model source-artifact clustering. There are only 57 held-out clean records, limiting specificity estimates. Short, self-contained artifacts omit industrial dependencies and runtime context. The retained length confound prevents interpreting binary detection as evidence of semantic understanding. Terminology Drift category names themselves reveal candidate answers, narrowing the category-agreement result. A single injected defect also leaves additional genuine findings hard to distinguish from false alarms.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 5 and 7, require shortcut baselines and explicit tests of the inference-label boundary before interpreting judge scores, and assess typed findings and evidence independently of binary detection. This narrows the synthesis claim "LLM-judge reliability can vary across benchmarks and perturbations even when the judge comes from a different model family." The negative benchmark finding can support a scoped warning; the usefulness of typed outputs does not license a claim that they improve binary accuracy or establish semantic reasoning. Hold an effectiveness endorsement until expert-validated, shortcut-resistant comparisons independently corroborate it. Expand-on: yes. Seed topics: shortcut-resistant specification judge benchmarks; independent validation of evidence-linked findings; executable leakage controls for evaluator pipelines.

## Claims Needing Human Review

- Whether the warning belongs under both explicit criteria and cross-family verification rather than primarily under benchmark construction.
- Whether the typed-finding measures justify any stronger statement than additional diagnostic information, given the single-defect annotations and category-vocabulary cue.
- Whether grade C with high confidence fits the inspectable controls despite synthetic labels and no stated release inspected here.
