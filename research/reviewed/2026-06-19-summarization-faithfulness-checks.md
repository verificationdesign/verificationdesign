# Summarization Faithfulness Checks

Reviewed: 2026-06-19
Reviewer: Human + Codex
Source: https://arxiv.org/abs/2111.09525
Evidence grade: B
Grade confidence: high
Disposition: held + expand-on (2026-06-28)

## Why It Matters

This source cluster gives external corroboration for a verification-design principle: an automated check that passes its own surface criteria does not mean it catches the failure class it claims to catch. It supports a planned canonical anti-pattern: a gate is not valid until it has been adversarially shown to catch its failure class. It also disconfirms the proposed automated fidelity gate for the held interview-pattern idea.

## Method / Evidence

Intrinsic errors are common in summarization faithfulness failures, not fringe cases. The FRANK taxonomy separates intrinsic semantic-frame and discourse errors from the single extrinsic Out-of-Article category [arXiv:2104.13346]. Intrinsic errors are roughly 30% of XSum and 50% of CNN/DM faithfulness errors [arXiv:2104.13346; arXiv:2205.12854].

Detector reliability remains well below human reliability. SummaCConv, the best NLI-based detector reported by SummaC after fixing the sentence-level versus document-level granularity mismatch, reaches 74.4% balanced accuracy averaged over six datasets [arXiv:2111.09525]. That still leaves roughly one in four cases misclassified.

The weakness is concentrated in the class that matters most here. Sentence-level entailment and QA-generation metrics are negatively correlated, and FactCC is nearly uncorrelated, with discourse and coreference attribution errors in FRANK [arXiv:2104.13346]. The narrower result is that dependency-level entailment has the highest correlation with discourse errors in the same paper, so not all entailment checks behave alike [arXiv:2104.13346].

Reliability is inflated for the fluent-rewrite regime. No single metric is superior across error types; balanced accuracy drops about 10 points from older summarizers to fine-tuned SOTA summarizers, and SummaC-style gains do not transfer to modern fluent outputs [arXiv:2205.12854].

Metrics also track surface form rather than meaning. They give inconsistent scores under meaning-preserving edits, can be gamed by appending content-free text, and are sometimes more sensitive to benign edits than to real factual corrections [arXiv:2411.16638]. The LLM-judge variant resists gaming best, but it over-relies on parametric knowledge rather than the provided source [arXiv:2411.16638].

## Limitations

The evidence comes from news and long-document summarization, including CNN/DM and XSum. Transfer to other authoring or rewriting settings is plausible but not directly tested. Quantifier, negation, and modality classes are only partially covered by these taxonomies.

One related source, the long-document stress test [arXiv:2511.07689], is a preprint. The rest of the cited work is peer reviewed through NAACL, TACL, ACL, and NeurIPS.

Metric reliability numbers are model-generation dependent and move over time. The disconfirming direction is stable even if the exact percentages are not.

## Suggested Update

Use this note to corroborate the planned canonical anti-pattern: a gate is not valid until adversarially shown to catch its failure class. The determinism case is the in-house worked example; this note is the independent corroboration. It also disconfirms an automated fidelity gate for the held interview-pattern idea.

2026-06-28: Disposition is held + expand-on. The fold into the canonical determinism-not-validity anti-pattern is deferred (maintainer decision); expand-on actively hunts independent, modern (LLM-judge-era) corroboration so the eventual fold does not rest on a pre-LLM-judge anchor. Registered seed topics in `research/scouts/config.json` under slug `summarization_faithfulness`: faithfulness evaluation, LLM judge faithfulness, factual consistency evaluation, claim-level verification, atomic fact verification, claim decomposition, groundedness evaluation, RAG faithfulness, answer groundedness, reference-free hallucination detection, reference-free faithfulness, factual consistency detection.

## Claims Needing Human Review

Whether grade B rather than C is right given the domain-transfer gap to non-summarization authoring.

Which of these papers, if any, should appear in the canonical References table when the anti-pattern is folded.
