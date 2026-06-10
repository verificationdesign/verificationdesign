# Backpressure

*(Orchestration Pattern)*

## Name

**Backpressure**

Also known as: Retry-with-Feedback, Rerun Context, Revision Loop.

## Intent

When a downstream check fails, route the failure back upstream as structured rerun context within a bounded retry budget, instead of swallowing the failure or retrying blindly.

## Problem

A downstream verifier fails. The system has several easy ways to lose that signal:

* log the failure and continue downstream;
* retry the same upstream call without telling it what failed;
* pass back a raw error string the upstream step cannot act on;
* keep retrying until a timeout or context budget stops the loop;
* ask the model to "try again" with no record of why.

That is upstream-unaware failure. The verifier found something, but the work step never receives a structured correction. The next attempt is sampled from the same prompt with the same blind spot. If it passes later, the system cannot tell whether the failure was fixed or merely disappeared.

`verification_design.md` Principle 6 names the core rule: executable verification is king. Backpressure is the orchestration move after that executable or rubric-backed verifier fails. The failure should block progress, become structured context, and drive a bounded rerun. Principle 3 supplies the step-level framing: failures are most useful when they are attached to the step that produced them, not discovered only at the end.

## Forces

* **Blind retry vs. feedback-carrying retry.** Blind retry may pass by chance. Feedback-carrying retry tells the upstream step what must change.
* **Bounded budget vs. unbounded loop.** Retry is useful only when capped.
* **Swallow failure vs. block progress.** Continuing downstream after failed validation turns a verifier into a logger.
* **Structured rerun context vs. raw error.** A typed failure can be consumed. A traceback may only confuse the next step.
* **Raise or escalate vs. silent give-up.** Exhaustion should become an explicit outcome, not a quiet stop.

## Solution

Feed the failure back to the producer.

The orchestrator runs the work step, runs the verifier, and if the verifier fails, formats the failure into rerun context. It invokes the work step again with that context and increments a retry counter. The loop stops only when the verifier passes or the budget is exhausted. On exhaustion, the system raises or escalates.

The model may revise the artifact. Code owns:

* the pass/fail criterion;
* retry count;
* maximum retries;
* failure context format;
* per-attempt verdicts;
* final outcome.

## Mechanism

1. **Run the work step.** Produce an artifact.
2. **Run the verifier.** The verifier returns a structured pass or failure with a reason.
3. **On failure, format rerun context.** Convert the failure into actionable context for the upstream step.
4. **Retry within a budget.** Reinvoke the upstream step with rerun context and increment attempts.
5. **Stop explicitly.** Proceed on pass; raise or escalate on exhaustion; record all attempts.

## Pattern / Antipattern

The same task: revise an output until a downstream validation passes or the retry budget is exhausted. The antipattern side is intentionally uncovered in this pass. The pattern side shows the failure becoming feedback within a counted budget.

### Antipattern: uncovered swallowed-failure instance

No strict Backpressure antipattern was promoted from the OSS bench surveyed for this catalog.

The natural failure shape is downstream-failure-swallowed, upstream-unaware: validation fails, but the system proceeds, logs only, or retries with no feedback context and no budget. That overlaps with **Adversarial Frame** when there is no failure-search rubric, so there is no structured failure to push back.

This card keeps the Antipattern instance empty rather than inventing one. When a strict instance is mined, re-author this section around the assertion `attempts > 1 and rerun_context is None`, or `verifier_failed and proceeded_downstream is True`.

### Pattern: bounded retry with structured feedback

The structured implementation formats verifier failure into rerun context and retries only within the budget.

```python
from dataclasses import dataclass
from typing import Literal


Outcome = Literal["passed", "raised_on_exhaustion"]


@dataclass(frozen=True)
class Verification:
    passed: bool
    reason: str


@dataclass(frozen=True)
class Attempt:
    index: int
    artifact: str
    verdict: str
    rerun_context: str | None


@dataclass(frozen=True)
class BackpressureResult:
    attempts: int
    max_retries: int
    rerun_context_fed_back: bool
    last_failure_reason: str | None
    per_attempt_verdicts: tuple[str, ...]
    outcome: Outcome
    artifact: str
    attempt_log: tuple[Attempt, ...]


def format_rerun_context(check: Verification) -> str:
    return f"Validation failed: {check.reason}. Revise only this failure."


def run_with_backpressure(work_fn, verify_fn, max_retries: int) -> BackpressureResult:
    rerun_context: str | None = None
    attempts: list[Attempt] = []
    last_failure_reason: str | None = None

    for attempt_index in range(1, max_retries + 2):
        artifact = work_fn(rerun_context)
        check = verify_fn(artifact)
        verdict = "pass" if check.passed else "fail"
        attempts.append(
            Attempt(
                index=attempt_index,
                artifact=artifact,
                verdict=verdict,
                rerun_context=rerun_context,
            )
        )

        if check.passed:
            return BackpressureResult(
                attempts=attempt_index,
                max_retries=max_retries,
                rerun_context_fed_back=any(a.rerun_context for a in attempts),
                last_failure_reason=last_failure_reason,
                per_attempt_verdicts=tuple(a.verdict for a in attempts),
                outcome="passed",
                artifact=artifact,
                attempt_log=tuple(attempts),
            )

        last_failure_reason = check.reason
        if attempt_index > max_retries:
            return BackpressureResult(
                attempts=attempt_index,
                max_retries=max_retries,
                rerun_context_fed_back=any(a.rerun_context for a in attempts),
                last_failure_reason=last_failure_reason,
                per_attempt_verdicts=tuple(a.verdict for a in attempts),
                outcome="raised_on_exhaustion",
                artifact=artifact,
                attempt_log=tuple(attempts),
            )

        rerun_context = format_rerun_context(check)

    raise AssertionError("unreachable")


def work_fn(rerun_context: str | None) -> str:
    if rerun_context is None:
        return "migration plan without rollback verification"
    return "migration plan with rollback verification"


def verify_fn(artifact: str) -> Verification:
    if "with rollback verification" in artifact:
        return Verification(passed=True, reason="")
    return Verification(passed=False, reason="rollback verification is missing")


result = run_with_backpressure(work_fn, verify_fn, max_retries=2)

assert result.attempts <= result.max_retries + 1
assert result.rerun_context_fed_back
assert result.outcome in {"passed", "raised_on_exhaustion"}
```

CrewAI task guardrails are the canonical instance for this card. A task can define guardrails and `guardrail_max_retries`; failed guardrails format validation error context, rerun the agent with that context, and raise when retry exhaustion is reached. The test suite covers both failure-then-success and max-retry exhaustion.

AutoGen's writer and critic loop is a partial instance. The critic's `APPROVE` token controls termination, so unresolved feedback keeps the writer/critic loop running. Dify's provider cooldown is analogy-grade: provider failures cool down a route and push the next attempt elsewhere, but that is infrastructure backpressure rather than agent-output backpressure.

## Determinism Move

Backpressure constrains `criteria_drift` by pinning the pass criterion and retry budget in code. A rerun is not driven by the model's sense that the output might be good enough now; it is driven by a recorded verifier result and a counted budget.

It also constrains `judge_subjectivity` when the backpressure signal comes from a real verifier: a guardrail, comparator, executable check, or adversarial rubric with explicit failure fields. A subjective "try again" prompt is not backpressure.

The determinism move is making the failure a counted, fed-back fact, so the rerun is caused by a recorded check result and a budget, not a retry impulse.

## Observable Signal

Every Backpressure report should include:

* attempts;
* maximum retries;
* rerun-context-present boolean;
* last failure reason;
* per-attempt verdicts;
* outcome, such as `passed` or `raised_on_exhaustion`;
* final artifact or escalation target.

A useful report shows the feedback loop:

```text
attempts: 2
max_retries: 2
rerun_context_present: true
last_failure_reason: rollback verification is missing
per_attempt_verdicts: [fail, pass]
outcome: passed
final_artifact: migration plan with rollback verification
```

## Failure Modes

* **Swallowed Failure:** downstream validation fails, but the pipeline proceeds. Make failure block progress.
* **Blind Retry:** the upstream step is retried without feedback context. Format the verifier failure into rerun context.
* **Unbounded Retry:** no retry budget exists. Record attempts and enforce `max_retries`.
* **Raw-Error Retry:** a traceback or unstructured string is passed upstream. Convert failure into fields the work step can act on.
* **Silent Exhaustion:** retry budget is exhausted and the system quietly stops. Raise or route to Escalation Chain.

## Use When

Use this pattern when:

* a downstream verifier can fail recoverably;
* the upstream step can consume corrective feedback;
* bounded automatic revision is cheaper than immediate escalation;
* a recorded retry trail is useful for audit or debugging;
* an Adversary, Comparator, or guardrail can produce a concrete failure reason.

## Do Not Use When

Do not reach for Backpressure when:

* the failure is non-recoverable and should escalate immediately;
* the upstream step cannot consume feedback;
* an Executable Analog passes deterministically without revision;
* retry cost is unacceptable;
* the verifier cannot state what failed.

If the failure cannot be turned into structured rerun context, route to Escalation Chain instead of looping.

## Evidence

* **Verification Design Principle 6:** the design doc treats executable verification as the strongest verification move; Backpressure makes a failed check drive bounded revision instead of being swallowed.
* **Verification Design Principle 3:** the same design doc frames verification as a step-level practice; Backpressure attaches failure to the step that produced it.
* **[CrewAI](https://github.com/crewAIInc/crewAI) task guardrails:** the orchestration sweep records a direct Backpressure instance: failed guardrails format validation error into rerun context, retry within `guardrail_max_retries`, and raise on exhaustion, with tests for both success-after-retry and max-retry failure.
* **[AutoGen](https://github.com/microsoft/autogen) writer and critic loop:** the orchestration sweep records a partial instance where critic feedback keeps the writer/critic loop running until explicit approval.
* **[Dify](https://github.com/langgenius/dify) provider cooldown:** the orchestration sweep records analogy-grade infrastructure backpressure: provider failures cool down the failing route and move subsequent attempts elsewhere.

## Related Patterns

* **Escalation Chain:** receives control when the retry budget is exhausted.
* **Adversary:** produces critic findings that can become the backpressure signal.
* **Adversarial Frame:** defines the failure-search rubric that gives the loop useful failures.
* **Comparator:** supplies the named operator that can drive pass/fail backpressure.
* **Causal Tag:** tags each retry attempt so the revision trail is auditable.
