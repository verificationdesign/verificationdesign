# Reward Bias Substitution: Single-Axis Bias Mitigations Redirect Optimization Pressure

Reviewed: 2026-06-09
Reviewer: Claude; human review pending
Source: https://arxiv.org/abs/2605.27996
Evidence grade: B
Grade confidence: medium

## Why It Matters

The canonical doc already argues that LLM judges are biased instruments and that executable checks beat patched judgment. This paper attacks the standard remedy directly: debiasing a reward model or judge along a single axis (length, sycophancy, style) cannot be certified from audit-distribution benchmarks, and can actively rotate optimization pressure onto correlated proxies instead of removing it. That turns "we debiased the judge" from a fix into an unverified claim, which is exactly the class of claim the doc tells builders to distrust.

## Method / Evidence

The paper formalizes mitigation outcomes into a regime taxonomy: successful mitigation, contaminated success, bias substitution, overcorrection, silent non-op, and audit-distribution sensitivity. Theorem 3.9 proves that successful mitigation, contaminated success, bias substitution, and overcorrection produce identical observables under any audit-distribution scoring, including ranking accuracy and win rate, even with oracle access to the true reward. Theorem 3.10 proves, under stated assumptions, that evaluating at policy-induced distributions while tracking multiple bias features suffices to separate the regimes.

Empirical demonstrations:
- GRPO length-penalty experiment (Llama-3.2-3B with Skywork-Reward-V2, 4 seeds per condition): the penalty compresses responses as intended (204 to 170 tokens) while expected calibration error rises from 0.25 to 0.41 and TriviaQA free-form accuracy falls from 56% to 42%. Length is suppressed; pressure rotates onto confidence.
- Best-of-N test of a published LOESS length-debiasing operator: it zeroes reward-length correlation on the audit distribution (0.316 to 0.037) but reintroduces length bias under best-of-N selection on three of four SOTA reward models, with AlpacaEval LC win rate degrading and GSM8K best-of-N accuracy dropping 3.6 points.
- Length-sycophancy coupling (over 14,000 responses across 8 model families): the measured effect of sycophancy on length changes sign between human-labeled, LLM-judge, and judge-disagreement regimes, demonstrating audit-distribution sensitivity.

## Limitations

Preprint (May 2026, v2 days after v1); no peer review or replication yet. This review read the arXiv HTML version in one pass, not an artifact audit. The paper's direct subject is reward-model bias mitigation in preference learning; applying it to verification-time LLM judges is a transfer step. The best-of-N selection results are the closest verification-time analog; the GRPO result is training-time. The authors note that first-moment drift can miss tail shifts for bounded features, that the spurious/structurally-relevant feature partition is binary, and that multi-axis certification remains incomplete even under policy-distribution evaluation.

## Suggested Update

Append a dated note under Principle 7 stating that single-axis judge or reward debiasing is not certifiable from audit-distribution benchmarks and can redirect bias rather than remove it; that certification requires evaluation under the distribution the optimized system actually induces, with multiple bias features tracked at once; and that this strengthens the existing preference for executable checks over patched judges. Add a References table row.

## Claims Needing Human Review

- Whether the transfer from reward-model mitigation to verification-time judge debiasing is characterized at the right strength. The best-of-N evidence is selection-time; the GRPO evidence is training-time; neither is literally an LLM judge in a verification harness.
- Whether the canonical note should carry the specific experimental numbers or keep them only in this review note.
- Whether the triage digest's alternative placement (extending the SycEval note under Principle 4) is preferable to Principle 7.
