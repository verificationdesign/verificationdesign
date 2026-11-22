# Beyond fabrication: Misattributed numbers in papers written by AI research agents

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.38691
Evidence grade: C
Grade confidence: high

## Why It Matters

A reported value can appear in an agent's artifacts under a different run, metric, or condition. Verification needs criteria for the relationship between the claim and its source. A strict provenance check also needs an unresolved outcome because traceable claims can fall outside its coverage.

## Method / Evidence

Read: arXiv v2 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Sampling and misattribution: the Into the Unknown benchmark contains 135 submissions. The authors label 256 extracted numbers from 18 submissions, oversampling certified claims by design. Of 53 unsupported claims, 47 are wrong-source and 6 have no identified support in the available files. The raw fraction is 47 of 53 (89%). The population-weighted share is 81%, the basis of the abstract's approximate finding. A missing entry leaves intent and unsaved computation unresolved.
- Annotation: the second annotator, a co-author, labels 48 confirmation claims while the first annotator is present without commenting. Following an AI-assisted rule-consistency review, the first annotator revises labels. On the raw double-labeled set, Cohen's kappa rises from 0.75 to 0.89 across all categories and from 0.83 to 0.96 for the binary traceability split.
- Strict checker: on the pooled 211 real claims, raw precision is 0.92 (78 of 85 certified) and raw recall is 0.49 (78 of 158 traceable). Population-weighted pooled recall is 0.35. On the held-out 60 real claims, raw precision is 0.93 (27 of 29 certified) and population-weighted precision is 0.95. Held-out weighted recall is 0.34, with 27 of 46 traceable claims certified in the raw labels. Among held-out claims left uncertified, 57% are traceable after weighting, with a raw fraction of 19 of 31.
- Comparison with model verification: on 129 real claims unused for tuning, strict precision and Claude Opus 5.5 verifier precision are both 0.89 unweighted (51 of 57 and 91 of 102 certifications respectively). Raw recall is 0.54 and 0.97, respectively, among 94 traceable claims. On the separate pooled set of 53 non-traceable claims, the verifier accepts 19 and the strict checker accepts 7. The second submission-level judge uses the same model as the verifier, from the same family as several judged agents. It passes 12 of 30 submissions against 6 of 30 under the official configuration, a raw paired comparison that also changes the harness and file access.
- Checkability: the deterministic checker matches values at reported precision, scores context in result entries, and compares the score with nearby numerical decoys. With the inputs and rules fixed, an independent run can reproduce which entries match and which claims are certified. The mechanism checks attribution to recorded evidence. Experimental validity and the completeness of the record require separate evidence.
- Reproducibility signals: the paper states that code, labels, derived data, and figures are publicly released and identifies the original benchmark release for raw submissions. These repositories were not opened for this review.
- Authority signals: the arXiv preprint lists university affiliations and names Data Science and Management in the journal field. The text gives no acceptance statement. These facts tune confidence and do not move the grade.

## Limitations

The benchmark-wide analysis covers 99 of 135 submissions. Exclusions are uneven across agents. The paper reports 15 timeouts, 2 failures, 16 storage exclusions, and 3 submissions without extractable claims. The checker relies on LaTeX and machine-readable outputs and omits integer-only values. Both annotators are on the research team and see candidate entries ranked by the retrieval procedure. The strict thresholds were frozen before annotation, while the evidence filter changed during development to exclude rendered paper text and build logs. Tooling and judge results are specific to this benchmark and its harnesses.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 5 and 6, require provenance checks to identify the run, metric, and condition behind a reported value and record unresolved claims for review. This narrows "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." The observed wrong-source cases establish a failure class for value-only matching. The proposed checker and combined review pipeline require independent corroboration for an effectiveness endorsement. Expand-on: yes. Seed topics: claim-level matching to execution artifacts; independent labeling of numerical provenance; coverage evaluation across research agent benchmarks.

## Claims Needing Human Review

- Whether the triage's "about four in five" needs an explicit weighting qualifier whenever cited, given the different raw share and the selected submissions.
- How much the selected evidence entries, annotator presence, and AI-assisted revision affect confidence in the labels used to estimate precision.
- Whether the ablation's pooled estimates should be cited alongside the frozen-threshold claim, given the indexing correction during labeling.
