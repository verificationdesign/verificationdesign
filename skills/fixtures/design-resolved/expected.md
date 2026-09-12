# Verification plan

Artifact: skills/fixtures/design-resolved/artifact

Scope: Verify the design-resolved pure square function against its exact integer specification, preserving the spec-stage judgment beside later build evidence.

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`

Corpus tag: `corpus/v1.0.0`

Skill: verification-design 1.3.0

Skill pins: catalog `b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f`; principles `03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a`

Generator model: unknown

Verifier model: fixture author, no model review

## Design

An agent generates a pure Python function returning the square of an integer in one step. A local assertion harness compares square(7) with 49 and square(-3) with 9 on every regression run; its exit code determines completion. The extractor is not yet written at design time; a later build will exercise it through the same assertions.

Source: artifact/workflow.md

## Verification requirements

### V1: The returned integer equals the expected integer on every regression run.

Run python3 artifact/check.py to compare square(7) with 49 and square(-3) with 9 by equality. Both equalities must hold to pass; any mismatch fails.

Patterns: [Comparator][comparator] ([pinned source][comparator-src])

### V2: The extractor, once written, is exercised by the same check.

Once the extractor exists, run python3 artifact/check.py and inspect its direct calls to the generated function and equality assertions. Pass when the same check exercises the returned values and both assertions hold; fail if extraction is bypassed or either comparison fails.

Patterns: none

## Assumptions

- verification-path: The executable fixture check and its documented completion signal.

## Measurements

- fixture-check: kind execution; env `{}`; exit 0; artifact revision ``; log none; note: Later fixture build ran with exit 0 and empty stdout; this does not rewrite the spec-stage verdict.

```text
python3 artifact/check.py
```

## Summary

Apply: 1; reject: 15; undecided: 1; unknown verdicts: 1.

Requirements: 2

Operator decisions:

- Executable Analog: the extractor would be more brittle than the LLM judgment it replaces Resolution recorded 2026-09-10.

Recommended order:

1. Comparator

## Workflow characterization

Generated: A pure Python square function.

Generator: A one-shot code-generating agent.

Completion signal: Planned local equality assertions exit successfully.

Self-review points:

None recorded.

## Patterns applied

### Comparator

[Comparator][comparator] ([pinned source][comparator-src])

Expected and observed integers are separate and equality is the named comparison operator.

Decision: apply

Serves: V1

- use_when: the check has a known expected value, pattern, reference object, or expected event sequence (holds). Evidence: artifact/workflow.md:3-16: Expected and observed integers are separate and equality is the named comparison operator.
- use_when: the observed value can be extracted separately from the comparison (holds). Evidence: artifact/workflow.md:3-16: Expected and observed integers are separate and equality is the named comparison operator.
- use_when: a named operator covers the comparison or can be defined cheaply (holds). Evidence: artifact/workflow.md:3-16: Expected and observed integers are separate and equality is the named comparison operator.
- use_when: the same comparison will run repeatedly in CI, regression tests, or agent loops. (holds). Evidence: artifact/workflow.md:3-16: Expected and observed integers are separate and equality is the named comparison operator.

Observable signals:

- operator name
- expected value or reference
- observed value extracted before comparison
- normalization steps applied before comparison
- notes for recorded parse or pattern failures
- score and threshold
- pass/fail verdict.

Determinism move: Comparator constrains `judge_subjectivity` by making the verdict a deterministic function of expected value, observed value, operator, threshold, and normalization. It constrains `criteria_drift` because a named operator is stable across runs in a way that a prompt-based judge's interpretation is not.

## Patterns rejected

### Constitution

[Constitution][constitution] ([pinned source][constitution-src])

The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.

- use_when: multiple agents or tools evaluate the same artifact (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs. Measurement fixture-check records the executable run.
- use_when: verification reports need to be auditable (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.
- use_when: criteria drift is causing inconsistent judgments (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.
- use_when: prompts contain repeated pass/fail language (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.
- use_when: failures must be compared across runs (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.
- use_when: human reviewers need to know what the system actually checked. (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.

### Guardrail Decorator

[Guardrail Decorator][guardrail-decorator] ([pinned source][guardrail-decorator-src])

No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.

- use_when: the framework supports lifecycle hooks at model, tool, retriever, or output boundaries (does-not-hold). Evidence: artifact/workflow.md:3-16: No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.
- use_when: policy enforcement gates side effects such as file writes, network calls, deletions, charges, sends, or deploys (does-not-hold). Evidence: artifact/workflow.md:3-16: No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.
- use_when: policy needs to survive prompt rewrites, persona tests, and context compaction (does-not-hold). Evidence: artifact/workflow.md:3-16: No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.
- use_when: audit requires a decision log per call (does-not-hold). Evidence: artifact/workflow.md:3-16: No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.
- use_when: the policy can be expressed as a deterministic decision function rather than a subjective judgment. (does-not-hold). Evidence: artifact/workflow.md:3-16: No lifecycle hooks, policy enforcement or model tool boundary exists; the function receives ordinary local integers.

### Causal Tag

[Causal Tag][causal-tag] ([pinned source][causal-tag-src])

No shared event surface or asynchronous work exists; each result is a private function return.

- do_not_use_when: the event surface is fully private to the test or run (holds). Evidence: artifact/workflow.md:3-16: No shared event surface or asynchronous work exists; each result is a private function return.
- do_not_use_when: the side effect is low stakes and misattribution cost is negligible. (holds). Evidence: artifact/workflow.md:3-16: No shared event surface or asynchronous work exists; each result is a private function return.

### Trajectory Cursor

[Trajectory Cursor][trajectory-cursor] ([pinned source][trajectory-cursor-src])

Generation is one-shot and the check has no agent decisions, retries or pause/resume path.

- do_not_use_when: the workflow is a single-shot model call with no loop (holds). Evidence: artifact/workflow.md:3-16: Generation is one-shot and the check has no agent decisions, retries or pause/resume path.
- do_not_use_when: the process is a deterministic transformation pipeline with no agent decisions (holds). Evidence: artifact/workflow.md:3-16: Generation is one-shot and the check has no agent decisions, retries or pause/resume path.

### State Baseline

[State Baseline][state-baseline] ([pinned source][state-baseline-src])

The property is internal to a deterministic function; there is no mutable environment.

- do_not_use_when: the verified property is purely internal to a deterministic function call (holds). Evidence: artifact/workflow.md:3-16: The property is internal to a deterministic function; there is no mutable environment.

### Blind Oracle

[Blind Oracle][blind-oracle] ([pinned source][blind-oracle-src])

Expected can be derived, but the executable assertion specializes the pattern and no model judge is used.

- do_not_use_when: Executable Analog can specialize the pattern with compilation, execution, or runtime traces (holds). Evidence: artifact/workflow.md:3-16: Expected can be derived, but the executable assertion specializes the pattern and no model judge is used.

### Delta

[Delta][delta] ([pinned source][delta-src])

No environmental metric or mutation exists; the only observation is a private function return.

- do_not_use_when: the environment is fully ephemeral (fresh container per run, mocked DB) (holds). Evidence: artifact/workflow.md:3-16: No environmental metric or mutation exists; the only observation is a private function return.
- do_not_use_when: the metric does not exist pre-action and only the absolute post-state is meaningful (holds). Evidence: artifact/workflow.md:3-16: No environmental metric or mutation exists; the only observation is a private function return.

### Judge Harness

[Judge Harness][judge-harness] ([pinned source][judge-harness-src])

Verification is executable and low stakes; no model judge or calibration set exists.

- do_not_use_when: verification is fully executable, so an Executable Analog or Comparator can decide it without an LLM (holds). Evidence: artifact/workflow.md:3-16: Verification is executable and low stakes; no model judge or calibration set exists.
- do_not_use_when: the verdict is low leverage and a single-sample judge call is proportionate (holds). Evidence: artifact/workflow.md:3-16: Verification is executable and low stakes; no model judge or calibration set exists.

### Admissibility Gate

[Admissibility Gate][admissibility-gate] ([pinned source][admissibility-gate-src])

The generated function has a directly executable correctness check; no model approval is needed.

- do_not_use_when: a named Comparator or Executable Analog can decide the check directly (holds). Evidence: artifact/workflow.md:3-16: The generated function has a directly executable correctness check; no model approval is needed.

### Cross-Family

[Cross-Family][cross-family] ([pinned source][cross-family-src])

No model judge evaluates the result; the local assertion decides it.

- do_not_use_when: verification is fully executable, so an Executable Analog or Comparator can decide it without an LLM judge (holds). Evidence: artifact/workflow.md:3-16: No model judge evaluates the result; the local assertion decides it.
- do_not_use_when: the verification is low leverage and misattribution cost is negligible (holds). Evidence: artifact/workflow.md:3-16: No model judge evaluates the result; the local assertion decides it.

### Adversary

[Adversary][adversary] ([pinned source][adversary-src])

The executable comparison decides the property without a critic role.

- do_not_use_when: the task is trivial and a second role would add process noise (holds). Evidence: artifact/workflow.md:3-16: The executable comparison decides the property without a critic role.
- do_not_use_when: an Executable Analog or Comparator can decide the property without an LLM critic (holds). Evidence: artifact/workflow.md:3-16: The executable comparison decides the property without a critic role.

### Debate

[Debate][debate] ([pinned source][debate-src])

The executable comparison decides the property without rounds or votes.

- do_not_use_when: an Executable Analog or Comparator can decide the property directly (holds). Evidence: artifact/workflow.md:3-16: The executable comparison decides the property without rounds or votes.
- do_not_use_when: token, latency, or provider cost cannot support multiple turns (holds). Evidence: artifact/workflow.md:3-16: The executable comparison decides the property without rounds or votes.

### Escalation Chain

[Escalation Chain][escalation-chain] ([pinned source][escalation-chain-src])

A failed check stops the local run; no handler hierarchy or automatic routing exists.

- do_not_use_when: a flat single-handler design is enough (holds). Evidence: artifact/workflow.md:3-16: A failed check stops the local run; no handler hierarchy or automatic routing exists.
- do_not_use_when: an Executable Analog or Comparator can decide the property without routing (holds). Evidence: artifact/workflow.md:3-16: A failed check stops the local run; no handler hierarchy or automatic routing exists.

### Backpressure

[Backpressure][backpressure] ([pinned source][backpressure-src])

The one-shot generator cannot consume check feedback; no revision loop is requested.

- do_not_use_when: the upstream step cannot consume feedback (holds). Evidence: artifact/workflow.md:3-16: The one-shot generator cannot consume check feedback; no revision loop is requested.

### Tool Adapter

[Tool Adapter][tool-adapter] ([pinned source][tool-adapter-src])

No model-produced tool arguments cross a boundary; the function is called internally.

- do_not_use_when: the call is fully internal and no model output crosses the boundary. (holds). Evidence: artifact/workflow.md:3-16: No model-produced tool arguments cross a boundary; the function is called internally.

## Not verified

### Executable Analog

[Executable Analog][executable-analog] ([pinned source][executable-analog-src])

Decision: undecided

- do_not_use_when: the extractor would be more brittle than the LLM judgment it replaces. Reason: artifact/workflow.md:7: the extractor is unwritten, so its brittleness relative to the model judgment cannot be judged until it exists.

Resolution (2026-09-10): The later fixture build uses direct integer assertions and both pass with exit 0. Evidence: artifact/check.py:1-6 records the function and assertions. Measurement: fixture-check

Determinism move: Executable Analog constrains `self_review_bias` (the same agent that produced the artifact no longer judges whether it satisfies the check) and `judge_subjectivity` (the verdict comes from a deterministic equality on extracted values, not from a model's interpretation of rendered output). By forcing extract-then-compare instead of interpret-and-decide, the system loses the freedom to rationalize a coincidental pass.

Instantiation: The fixture check emits a pass only after its asserted comparison holds.

```json
{
  "unavailable": true,
  "source_url": "https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md",
  "reason": "offline"
}
```

## Sources

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`.

Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).

[principles]: https://verificationdesign.com/principles/
[principles-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md
[comparator]: https://verificationdesign.com/patterns/verification/comparator/
[comparator-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/comparator.md
[constitution]: https://verificationdesign.com/patterns/context-and-state/constitution/
[constitution-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/constitution.md
[guardrail-decorator]: https://verificationdesign.com/patterns/context-and-state/guardrail-decorator/
[guardrail-decorator-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/guardrail-decorator.md
[causal-tag]: https://verificationdesign.com/patterns/context-and-state/causal-tag/
[causal-tag-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/causal-tag.md
[trajectory-cursor]: https://verificationdesign.com/patterns/context-and-state/trajectory-cursor/
[trajectory-cursor-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/trajectory-cursor.md
[state-baseline]: https://verificationdesign.com/patterns/context-and-state/state-baseline/
[state-baseline-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/state-baseline.md
[blind-oracle]: https://verificationdesign.com/patterns/verification/blind-oracle/
[blind-oracle-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/blind-oracle.md
[delta]: https://verificationdesign.com/patterns/verification/delta/
[delta-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/delta.md
[judge-harness]: https://verificationdesign.com/patterns/verification/judge-harness/
[judge-harness-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/judge-harness.md
[admissibility-gate]: https://verificationdesign.com/patterns/verification/admissibility-gate/
[admissibility-gate-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/admissibility-gate.md
[cross-family]: https://verificationdesign.com/patterns/orchestration/cross-family/
[cross-family-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/cross-family.md
[adversary]: https://verificationdesign.com/patterns/orchestration/adversary/
[adversary-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/adversary.md
[debate]: https://verificationdesign.com/patterns/orchestration/debate/
[debate-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/debate.md
[escalation-chain]: https://verificationdesign.com/patterns/orchestration/escalation-chain/
[escalation-chain-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/escalation-chain.md
[backpressure]: https://verificationdesign.com/patterns/orchestration/backpressure/
[backpressure-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/backpressure.md
[tool-adapter]: https://verificationdesign.com/patterns/orchestration/tool-adapter/
[tool-adapter-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/tool-adapter.md
[executable-analog]: https://verificationdesign.com/patterns/verification/executable-analog/
[executable-analog-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/executable-analog.md
