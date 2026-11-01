# Evaluate the Stack, Not the Layer: Do Deterministic and LLM Gates for Agent Actions Fail Independently?

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.07359
Evidence grade: C
Grade confidence: medium

## Why It Matters

This study tests the error multiplication assumption behind stacked action gates. It directly narrows Principles 2 and 7: separate implementations and different judge vendors do not establish independent verification. Joint misses, marginal failure rates, corpus coverage, and the treatment of human escalation must be measured together. The study also shows why improving a layer's solo accuracy need not add coverage to an existing stack.

## Method / Evidence

Read: arXiv v2 abstract and full paper (local text extraction, 2026-11-01).

- Population: 1,119 authored actions comprise internal, independent, and external corpora of 300, 630, and 189 cases. Joint misses are measured on 560 block cases; false alarms on 379 allow cases. The 180 warn cases belong to neither error domain. There is no adaptive adversary.
- Stack: a deterministic layer with 174 regular-expression rules and four chat-model judges produces allow, warn, block, or review verdicts. The primary panel combines an archived GPT-5.5 column with recollected Haiku, Sonnet, and Opus tiers. PRIMARY counts review as caught; STRICT counts it as a miss because escalation does not itself stop an action.
- Headline joint-error result: under STRICT, judge pairs provide 1.22 to 1.44 multiplication-equivalent layers, while rule-plus-judge pairs provide 1.86 to 2.09. On the pooled block population, median miss correlation is +0.430 for judge pairs and +0.014 for rule-plus-judge pairs; significant associations occur in 6 of 6 judge pairs and 0 of 4 rule pairs. These results do not establish statistical independence.
- A PRIMARY illustration makes the denominator explicit: a rule-plus-judge pair jointly misses 7 of 560 block cases (1.3%), whereas a judge pair jointly misses 29 of 560 (5.2%) against a multiplication prediction of 1.1%. Pair selection and miss definition matter; these are not universal stack failure rates.
- Negative result: adding a cloud rule pack reduces solo rule miss rate from 0.139 to 0.111 but adds zero new joint coverage over the three-judge baseline under either definition. Clean-provenance cross-vendor comparisons show no reported cross-vendor advantage. Version logging found an unrequested served model in 50 of 112 batches for one tier; changing review accounting reversed five conclusions.
- Checkability: joint-miss intersections, marginal rates, correlation, and multiplication-equivalent layer counts can be recomputed from fixed per-case verdicts. This arithmetic does not verify corpus labels, action realism, downstream human decisions, or an explanation of why judges co-fail. Difficulty attribution remains non-identifiable.
- Reproducibility signals: the paper states that a public evaluate-the-stack repository contains verdict matrices, per-call provenance, deterministic analysis scripts, audit summaries, and withdrawn conclusions. Case texts, embedded prompts, raw responses, the external corpus, and collection scripts are available on request rather than included in that artifact. Some case-dependent analyses cannot be recomputed from the public files.
- Authority signals: this is an arXiv preprint with a university affiliation; the inspected text supplies no peer-review acceptance claim. Affiliation and publication status tune confidence and do not move the evidence grade.

## Limitations

The internal corpus tuned the rules, and the independent corpus was retained through rule patches, so its residual is not zero-shot rule performance. Only the external corpus tests the semantic-threat setting discussed by the authors. Per-corpus intervals overlap, sparse joint misses censor some estimates, and a full-stack point estimate is unreliable. No human review layer was measured. The archived judge lacks collection provenance, and recollection conditions are not identical beyond case blocks. The difficulty share ranges from 31.8% to 61.8% across probes and accounting conventions; residual coupling cannot identify a shared mechanism. Other deterministic mechanisms and adaptive adversaries remain untested.

## Suggested Update

Disposition: fold-a-narrow-warning. Principles 2 and 7 should require observed joint coverage and explicit escalation semantics before treating a stack as independent. This would narrow "LLM-judge reliability can vary across benchmarks and perturbations even when the judge comes from a different model family." The checkable joint-error mechanism supports the warning, while claims that deterministic layers generally decorrelate need independent corroboration beyond this rule engine and these corpora. No canonical edit is made here. Expand-on: yes. Seed topics: joint misses in agent gate stacks; escalation semantics in verification evaluation; mechanism diversity and error correlation.

## Claims Needing Human Review

- Whether triage's closer-to-independent description needs stronger qualification for corpus-specific intervals and rule tuning.
- Whether the cloud-pack counterexample supports the proposed marginal-coverage warning without implying that rule augmentation is generally redundant.
- Whether grade C and medium confidence properly account for disclosed provenance defects and partially public artifacts.
