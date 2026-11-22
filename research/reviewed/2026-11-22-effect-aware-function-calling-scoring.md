# CAREFUL-Bench: Effect-Aware, Judge-Free Evaluation of Multi-Turn LLM Function Calling

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.02978
Evidence grade: C
Grade confidence: medium

## Why It Matters

A tool trajectory can reach the required final state while performing surplus or unauthorized work. Replaying the calls and checking their effects makes this distinction observable. Reference trajectories provide the comparison in this study, so the validity of the effect score depends on what those trajectories encode about the request.

## Method / Evidence

Read: arXiv v2 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Effect inference and scorer. The authors sampled simulator states and measured changes after calling each of 128 BFCL functions. Repeating a call provided evidence about idempotence on the observed states. Of four annotators for destructive effects, two were authors and two were models from one vendor. The final policy included any function that any annotator classified as destructive. Conditions were generated using the preliminary boundary and scored using the final one. A release test reportedly reproduced BFCL results and final states on all 800 reference trajectories.
- Ranking and gaps. In the HTML full text, base-category rank correlation is 0.98 over 11 open models, and the four-category mean has correlation 1.00 for those models. On 200 base conversations, the leader by BFCL accuracy, Llama-xLAM-2-8B, scored 77.0 officially and 62.5 under effect safety, a within-run loss of 14.5 percentage points associated with 48 collateral calls. The standard protocol also includes two API models. Claude Sonnet 5.5 and Llama-xLAM-2-8B swap order under effect safety when API models are included.
- Hints and confirmation. Advisory hints yielded no statistically significant accuracy change in the paired comparisons for seven open models and Claude Haiku 5.5. With the answering user, Haiku gained 84 and lost 49 of the same 800 conversations (p=0.003). Of 712 conversations with a required destructive action, Haiku completed 6 with every destructive call confirmed and no collateral call. No model exceeded that count, and the separate base-only Sonnet trial covered 178 such conversations and had no strict successes. The authors attribute the principal performance gain to clarification.
- Checkability. Call-by-call replay against pinned simulators lets a reviewer recalculate collateral calls, duplicate writes and final scores from logs. The simulator exposes modeled state changes. The scope of actual authorization still depends on reference calls, effect labels and the granularity at which confirmation is checked.
- Reproducibility signals. The paper states that it releases effect declarations and labels, the scorer, protocol and scripts under Apache-2.0, with the benchmark version pinned. The HTML gives no release URL, and no release was opened.
- Authority signals. The paper is an arXiv preprint from two university-affiliated authors. Affiliation and venue status tune confidence. The evidence grade reflects the benchmark design and scope.

## Limitations

The accuracy columns are single runs. Between runs of the same open model, 22 to 147 of 800 verdicts changed, large relative to many condition differences. Simulator state omits some consequences, and sampled idempotence remains conditional on the sampled states. The scripted user can recognize the right function while missing wrong arguments, limiting conclusions about consent to a specific effect. Scoring extra destructive functions against a reference multiset also leaves room for semantically different calls with the same function count.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 3 and 6, the base-category score gap extends "Tool-use verification can evaluate local action errors separately from failures in multi-step rollouts." In this example, the study distinguishes final-state correctness from collateral actions within a rollout. It corroborates the request-to-effect motivation of "Intent-Governed Tool Authorization for AI Agents" by showing a distinct failure class under final-state scoring. The replay study neither tests the gateway nor establishes that effect declarations and a simulated approval enforce actual request bounds. Hold the behavioral effectiveness claims pending independent evidence. Expand-on: no.

## Claims Needing Human Review

- The triage label narrows fits, but its 14.0-point paraphrase follows the abs page. The v2 abs page pairs 14.0 with 0.99, while the HTML headline gives 14.5 and 0.98. The sensitivity analysis uses a different model population and boundary variants.
- The prose's read/write split and Table 2 totals do not reconcile. The count is omitted here. The introduction also describes majority annotation, while the detailed method specifies the final any-annotator rule.
- Confirm that the warning remains scoped to replay against benchmark-defined effects, and that the different population for the API-inclusive ranking is explicit.
