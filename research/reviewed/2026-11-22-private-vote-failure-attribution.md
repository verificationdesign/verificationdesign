# POIROT: Agents as their own auditors for failure attribution in large language model multi-agent systems

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2606.02282
Evidence grade: C
Grade confidence: medium

## Why It Matters

Agents that participated in a failed run can have different views of its records. Pooling private diagnoses may preserve information that becomes less useful after participants see a common summary. The relevant outcome is exact attribution against external labels, which lets a study measure whether agreement tracks the component that caused the failure.

## Method / Evidence

Read: arXiv v2 abstract and full paper (arXiv HTML, local text extraction, 2026-11-22).

- Population: each model is tested on the same 121 cases from the algorithm-generated Who&When subset, scored for responsible-agent attribution. The synthetic BLAME trials use RehabTeam, with 10 trials per scenario and 150 total per model and condition, and TradingAgents, with 17 trials per error vector and 102 total. The backbones are DeepSeek V4.1 Flash, GPT-OSS 120B, and GPT-OSS 20B.
- Scoring: accuracy is exact match on the full binary attribution vector. An external space constructor enumerates candidate components. The protocol aggregates private votes and marks the top k components, where k is the true culprit count. The published prompt for the same-backbone, all-at-once external evaluator gives the size and positions of the hazard space and allows multiple marked components. It supplies no case-specific culprit count or fixed output cardinality.
- Full protocol: C3 includes shared assessment summaries and peer interrogation before voting. C3 exceeds the single-evaluator baseline in eight of nine model-benchmark configurations. On the 121 Who&When cases with DeepSeek, C3 scores 57.9% against 30.6% for the baseline.
- Private assessment: C1 keeps self-assessment private through voting. C1 exceeds the single-evaluator baseline in all nine configurations, significantly in eight. On the 102 TradingAgents trials per model, C1 with GPT-OSS 120B scores 83.3% against 33.3% for the baseline.
- Interaction ablation: on the same TradingAgents trials, showing a shared summary before voting in C2 reduces DeepSeek and GPT-OSS 120B accuracy by 49.0 percentage points each relative to C1. Unanimity increases from C1 to C2 in all nine configurations. C3 interrogation recovers part of the loss for those two TradingAgents models, but C3 never significantly outperforms C1 and is significantly worse in four configurations. No ablation step has a significant effect on Who&When. Replacing the hazard-aware weights with uniform weights changes no aggregate attribution in any benchmark, model, or condition.
- Checkability: benchmark labels and saved vote vectors permit independent tallying, exact-match scoring, and comparison of the private and shared conditions. The released records could also show which components acquired votes after summary sharing. Those checks are conditional on the labels and supplied culprit count. Attribution when the count is unknown would require another test.
- Reproducibility signals: the paper describes public BLAME fixtures and logs, raw results, regeneration scripts, an open-source protocol library, and prompts in the supplement. The linked repositories were not opened.
- Authority signals: the arXiv preprint lists public-research and university affiliations with no peer-reviewed acceptance stated. These facts inform confidence. The grade follows study design and coverage.

## Limitations

The authors select C1 from the ablation and compare it with the baseline on the same cases and trials. The text describes no held-out set for that comparison. Who&When and TradingAgents reuse archived sessions for the voting ablations, while RehabTeam runs each condition end to end. Every LLM call uses temperature 0. The paper describes repeated BLAME trials and archived voting replays, but gives no trial-level account of what inputs or execution settings vary within each fault scenario. Private diagnoses can still share a backbone and underlying evidence. Repeated trials and synthetic faults provide evidence for the selected environments. Scoring relies on expert annotations or known injected faults, and access to the true culprit count narrows the practical inference.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 2 and 8, use private attribution as a baseline when adding shared summaries or interrogation, and report exact-match accuracy alongside unanimity. The warning applies to failure attribution and qualifies where a separate evaluator may be useful. Any claim that private pooling can replace an external evaluator in deployment should wait for held-out corroboration with equivalent information, including how each protocol obtains its culprit count. Expand-on: yes. Seed topics: held-out multi-agent failure attribution; private voting with unknown culprit counts; shared summaries and attribution herding.

## Claims Needing Human Review

- The triage label challenges is broader than the result. The comparison bears on private pooling versus discussion and a particular external diagnosis baseline. It leaves verification conditioned on another agent's draft and adversarial debate with a judge untested.
- The extraction left baseline access to the culprit count open. Appendix B.4 gives the evaluator no explicit count, while Phase V uses the ground-truth count. Check the comparison under equivalent access to culprit counts and on new sessions, and check the released logs for the source of variation between trials.
- The triage description of harm from sharing and failure to recover is strongest for TradingAgents. Check the scoped wording given the inconclusive Who&When ablations and the partial C3 recovery on TradingAgents. The prose describes no cases fixed in the severe C1-to-C2 drops, while Table S5 reports 1% fixed for DeepSeek.
