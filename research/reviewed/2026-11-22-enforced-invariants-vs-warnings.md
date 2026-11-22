# Invariant-Aware Harness Enforcement to Protect LLM Agents from Silent API Failures

Reviewed: 2026-11-22
Reviewer: Codex draft; human review pending
Source: https://arxiv.org/abs/2611.20595
Evidence grade: C
Grade confidence: medium

## Why It Matters

An agent can receive evidence that a tool result failed a check and still use that result in its answer. SilentGuard moves the decision into the harness. Its evaluation makes the consequences of that decision measurable: the harness can reduce the release of wrong answers by returning fewer answers overall.

## Method / Evidence

Read: arXiv v1 abstract and paper text with adversary-procedure passages excluded from the read (raw lines 1138-1181, 1191-1293, 1511-1535, 1613-1614, 1670-1737, 3049-3053, 3119-3125); results, design, limitations and remaining appendices read (arXiv HTML, local text extraction, 2026-11-22).

- Population and design. AgentOrchBench uses synthetic catalog counts with exact ground truth from seed data. The experiment uses 36 tasks with 2 seeds per fault type or clean condition, per model and method arm. The harness rechecks a failed result and withholds values when an exact check fails again. A learned check can trigger a warning. A count answer must be backed by a checked count or the harness can return unknown.
- Enforcement, warning, and coverage. On the six targeted fault types across 7 open models, unguarded runs yielded 74.0% wrong answers. A warning from the same full check yielded 70.1% wrong, and a warning with permission to abstain yielded 18.2% wrong. The SilentGuard arm in Table 3 yielded 1.7% wrong, 95.8% unknown, and 2.4% correct. The no-guard arm yielded 16.4% correct on faulted runs. Wrong excludes unknown, so the decrease in wrong answers measures fewer wrong releases while accuracy on faulted runs also falls. Clean accuracy was 84.9% with SilentGuard and with no guard.
- Judge comparison. The advisory LLM judge already sees the harness check results and leaves 71.2% of faulted runs wrong. With that evidence and blocking the wrong share is 6.1%. The separate judge without check evidence leaves 71.7% wrong when advising and 70.8% when blocking. All are AgentOrchBench means over the open models.
- Coverage boundary. Six fault types introduced after the method freeze were evaluated on 36 tasks each with the harness alone and no model. Wrong answers fell from 61.1% to 24.5%, while correct answers fell from 38.9% to 19.0%. The remaining wrong answers came from faults the check missed. Clean-input cost also varies by benchmark. On ToolMaze, where the learned checks issue warnings, clean task success was 4.6 percentage points below Outcome Monitors.
- Other populations. The read-only probe found at least one silent fault in 11 of 15 public APIs. The separate agent study used 9 public APIs and 45 runs per model, arm, and documentation version. With slightly wrong documentation, the open-model wrong share was 89.8% without a guard, 21.3% with SilentGuard, and 21.0% with the published-parameter check alone. The paper's prose reports 70.2% to 0.5% wrong on targeted AgentOrchBench faults for three frontier models, added after the planned experiments.
- Checkability. For a stable, two-valued filter, a count under a condition and the count under its complement should sum to the count for the same query with that condition removed. This relation can be checked independently of the agent. The harness action and answer decision can be replayed against known benchmark counts. Consistency leaves the ground-truth count and the agent's fidelity to the requested query unverified.
- Reproducibility signals. The paper reports a public code repository with synthetic services and data, tasks, predictions, and hashes, and a separate public dataset. It offers external-run logs on request. Those artifacts were outside the materials inspected here.
- Authority signals. This arXiv preprint lists university and industry affiliations. These facts tune confidence. The grade rests on the method and scope of the evidence.

## Limitations

The targeted comparison uses the authors' count tasks and recurring fault classes. A consistent wrong result can satisfy the count identity, and changing totals or missing values can invalidate its assumptions. The frontier runs and the Nemotron control runs lack releasable logs, hash records, and pre-written predictions. The excluded raw passages cover procedural fault material and prompt text. The exclusion limits review of benchmark construction and the exact wording of intervention arms.

## Suggested Update

Disposition: fold-a-narrow-warning. For principles 3 and 6, require evidence that a checkpoint's failed verdict governs the release decision and measure wrong, unknown, correct, and clean outcomes. For recurring faults detectable by these checks, the matched enforced-versus-advisory comparison supports the claim "A deterministic or automated gate can satisfy its surface metric while missing the failure class it is meant to detect." The release of read results also suggests an analogy to "Operator-facing approval, cancellation, timeout, and authorization controls govern external effects only when the enforcement path completely mediates those effects." Transfer beyond those conditions needs corroboration. Expand-on: yes. Seed topics: enforcement against advisory checkpoints; invariant blind spots in tool results; abstention and clean-input costs.

## Claims Needing Human Review

- Check that the triage's warning and enforcement contrast is read alongside the decline in correct counts under faults and the harness-only result on unseen fault types.
- Check whether the general gate claim is the right home for the evidence and whether to keep the read-result analogy to the external-effects claim.
- Before treating the frontier mean as corroboration, assess how the missing logs, hash records, and predictions limit independent inspection.
