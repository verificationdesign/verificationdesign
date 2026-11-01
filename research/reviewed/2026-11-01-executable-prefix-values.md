# Executable Prefix Values for Locating Agent Failures

Reviewed: 2026-11-01
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2610.17633
Evidence grade: C
Grade confidence: medium

## Why It Matters

Executable prefix values compare a plausible failure annotation with the probability that an agent actually succeeds when resumed from that state. This narrows Principles 3 and 6: a checkpoint that recognizes an apparent mistake may not locate a useful intervention point. The paper makes a counterfactual outcome measurable, while retaining dependence on the chosen policy, environment reconstruction, budget, and task evaluator.

## Method / Evidence

Read: arXiv v1 abstract and full paper (local text extraction, 2026-11-01).

- Setup: on 150 SWE-bench Verified tasks, frozen Qwen3.6-27B and Qwen3.5-9B policies use the mini-swe-agent scaffold. The main policy produces 1,200 base runs, with a step budget of 100. Failed trajectories are selected from tasks with 2 to 6 successes in 8 runs, rather than all failures. Replay and back-filling yield 47 main-policy and 60 second-policy trajectories.
- Measurement: the authors reconstruct intermediate states, replay recorded commands, check observations and state fingerprints, and sample fresh continuations under the remaining budget. Adaptive screening, bisection, confirmation, and label probes estimate success curves. A point of no return is certified against an upper confidence bound, rather than inferred from a transcript's apparent error.
- Headline localization result: four main judges return 188 answers on the 47 failed main-policy trajectories, of which only 7 name the decisive step. Of 95 distinct labeled steps probed on both sides, 64 (67%) show no success-probability drop. Across the 162 non-abstaining labels, 107 are zero-drop and 132 (81%) are post-cause or zero-drop. These denominators distinguish distinct steps, labels, and all answers.
- Negative controls: GPT-6.1 Sol and GPT-6 Astra each flag 8/10 successful decoys on the main policy and 10/10 on the second policy. On the latter's 60 failed trajectories, 166/217 labels are post-cause or zero-drop, and only 14/240 answers name the decisive step. A successful run can contain an apparent mistake without justifying a restart.
- Restart result: offline expected success on affected main-policy tasks rises from 0.44 to 0.57 using the measured restart point; judge-label policies change it by -0.08 to -0.03. This calculation assumes value-based policies never restart runs that would succeed. In the separate online check, 240 fresh runs from restart decisions on 30 selected trajectories achieve 0.39 success, against predicted 0.45 and estimated continuing value 0.26. This is a selected restart check, not a deployed controller evaluation.
- Measurement limit: even the full schedule identifies the decisive step exactly in only 28% of parametric-bootstrap replications. On the second policy, 58% of continuations exhaust the remaining budget, and restoring the full budget moves the decisive step later in all 10 checked trajectories. The executable reference itself has uncertainty.
- Checkability: replayed state fingerprints, fresh continuations, and official task-test outcomes make prefix success empirically reproducible. They measure loss relative to a fixed policy and budget, not an unconditional semantic cause or the earliest logically wrong action. Passing tests does not prove that every patch is correct beyond the evaluator.
- Reproducibility signals: the paper states that code, curves, and labels are released, supplies an anonymous codebase URL, and refers to a released revision manifest. This review did not obtain or execute the artifacts and therefore does not claim reproduction.
- Authority signals: this is an arXiv preprint with university and independent-researcher affiliations; the text supplies no peer-review acceptance statement. These facts tune confidence and do not move the evidence grade.

## Limitations

Both policies belong to the same model family and share a scaffold and benchmark subset. Replay excludes genuinely nondeterministic trajectories, so reconstructable failures are a selected population. Isotonic fitting can flatten real recoveries. The main judge panel comes from a single vendor; the separate cross-family annotator and human are not interchangeable with that panel. Budget exhaustion especially constrains the second policy. Offline restart gains rely on an optimistic successful-run assumption, and the online experiment does not remove that assumption for an operational controller. Curve construction is expensive, and exact-step uncertainty limits causal wording.

## Suggested Update

Disposition: fold-a-narrow-warning. For Principles 3 and 6, require intervention-based validation before treating a judged first mistake as the right checkpoint or restart target. This would narrow "Tool-use verification can evaluate local action errors separately from failures in multi-step rollouts." The checkable outcome contrast warrants a warning scoped to the tested coding agents; hold general controller effectiveness and universal causal-localization claims pending independent corroboration. No fold is performed here. Expand-on: yes. Seed topics: executable counterfactual agent restarts; budget-sensitive failure localization; independent prefix-value measurement.

## Claims Needing Human Review

- Whether grade C and medium confidence adequately reflect the replay exclusions and the second policy's failed budget check.
- Whether the causal language should be restricted further to policy-relative success loss, retaining triage's narrowing label.
- Whether the abstract's zero-drop headline should be avoided in favor of the explicit distinct-step and label denominators used here.
