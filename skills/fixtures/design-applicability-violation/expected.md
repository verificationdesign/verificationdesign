# Verification plan

Artifact: skills/fixtures/design-applicability-violation/artifact

Scope: Verify the pure square function against its exact integer specification.

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`

Corpus tag: `corpus/v1.0.0`

Skill: verification-design 1.3.0

Skill pins: catalog `b1d737c5ea62e18fc276b8efe64d963e1326c7f93c8b2e639515ed2583ce2d3f`; principles `03033f7084e8fee60e5f7fff7249238af9f375942ad856d4cf485d22d68bf61a`

Generator model: unknown

Verifier model: fixture author, no model review

## Design

An agent generates a pure Python function returning the square of an integer in one step. A local assertion harness compares square(7) with 49 and square(-3) with 9 on every regression run; its exit code determines completion. In this hypothetical variant, adapting the general Comparator costs more than one-off human review.

Source: artifact/workflow.md

## Verification requirements

### V1: The returned integer equals the expected integer on every regression run.

Run python3 artifact/check.py to compare square(7) with 49 and square(-3) with 9 by equality. Both equalities must hold to pass; any mismatch fails.

Patterns: [Executable Analog][executable-analog] ([pinned source][executable-analog-src])

### V2: The check exits non-zero on any mismatch and the run log records it.

Run the assertion harness with a mismatching return and capture its exit code and failure output in the run log. Pass only when the exit code is non-zero and the log records the mismatch; a zero exit or missing failure record fails. This failure-path log check is planned, not recorded as executed.

Patterns: none

## Assumptions

- verification-path: The executable fixture check and its documented completion signal.

## Summary

Apply: 1; reject: 16; undecided: 0; unknown verdicts: 0.

Requirements: 2

Operator decisions:

None.

## Workflow characterization

Generated: A pure Python square function.

Generator: A one-shot code-generating agent.

Completion signal: Existing local equality assertions exit successfully.

Self-review points:

None recorded.

## Patterns applied

### Executable Analog

[Executable Analog][executable-analog] ([pinned source][executable-analog-src])

An assertion compares the pure function result against a specified integer, repeatedly in a local regression check.

Decision: apply

Serves: V1

- use_when: the claim being verified can be expressed as a deterministic check (holds). Evidence: artifact/workflow.md:3-16: An assertion compares the pure function result against a specified integer, repeatedly in a local regression check.
- use_when: the output has structure (DOM, JSON, exit code, log line) that can be queried (holds). Evidence: artifact/workflow.md:3-16: An assertion compares the pure function result against a specified integer, repeatedly in a local regression check.
- use_when: you can write a test rather than just describe one (holds). Evidence: artifact/workflow.md:3-16: An assertion compares the pure function result against a specified integer, repeatedly in a local regression check.
- use_when: the same check will run repeatedly (regression, CI, multi-agent loops) (holds). Evidence: artifact/workflow.md:3-16: An assertion compares the pure function result against a specified integer, repeatedly in a local regression check.

Observable signals:

- check_id: the named check being run
- expected: the value the executable analog is checking against
- observed: the raw value returned by the extractor, before judgment
- passed: the strict comparison result
- error: the exception text when extraction fails, otherwise None.

Determinism move: Executable Analog constrains `self_review_bias` (the same agent that produced the artifact no longer judges whether it satisfies the check) and `judge_subjectivity` (the verdict comes from a deterministic equality on extracted values, not from a model's interpretation of rendered output). By forcing extract-then-compare instead of interpret-and-decide, the system loses the freedom to rationalize a coincidental pass.

## Patterns rejected

### Constitution

[Constitution][constitution] ([pinned source][constitution-src])

The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.

- use_when: multiple agents or tools evaluate the same artifact (does-not-hold). Evidence: artifact/workflow.md:3-16: The small local harness has one executable check, no audit report consumer, no drifting prompt criteria and no comparison of failures across runs.
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

### Comparator

[Comparator][comparator] ([pinned source][comparator-src])

The one-off cost exclusion holds despite applicable comparison conditions.

- do_not_use_when: designing a comparator costs more than a one-off human review (holds). Evidence: artifact/workflow.md:18-19 explicitly states that a general Comparator costs more than one-off human review.

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

None in the judgment record.

## Sources

Corpus revision: `e632a86b2ca8fbb7f83b3130ba083784c7817667`.

Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).

[principles]: https://verificationdesign.com/principles/
[principles-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/verification_design.md
[executable-analog]: https://verificationdesign.com/patterns/verification/executable-analog/
[executable-analog-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/executable-analog.md
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
[comparator]: https://verificationdesign.com/patterns/verification/comparator/
[comparator-src]: https://raw.githubusercontent.com/verificationdesign/verificationdesign/e632a86b2ca8fbb7f83b3130ba083784c7817667/ai-design-patterns/cards/comparator.md
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
