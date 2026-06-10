# Delta

*(Verification Pattern)*

## Name

**Delta**

Also known as: Baseline Assertion, Relative State Verification, Ambient Isolation.

## Intent

Verify the success of an agent's actions by asserting on the *change* in environment state rather than the *absolute* environment state.

## Problem

Agentic systems often operate in shared, messy, or long-lived environments (databases, CI/CD runners, live cloud accounts). When a verification step checks for an absolute threshold (e.g., `total_flows >= 5` or `task_status == "completed"`), it is vulnerable to ambient state contamination.

If the system already had 5 flows before the agent acted, the assertion passes trivially. The verification system creates a green report, but it proved absolutely nothing about the agent's actions. Because agents can rationalize a coincidental pass as "my action succeeded," they are blind to the fact that their tools actually failed or were never called.

## Forces

* **Shared vs. Ephemeral Environments.** Spinning up a perfectly clean, mocked environment for every agent action is computationally expensive and sometimes impossible; operating in dirty environments requires careful state isolation.
* **Absolute vs. Relative logic.** It is easier to write `assert count == 10` than to capture a pre-state, pass it through the workflow, and write `assert post_count - pre_count == 10`.

## Solution

Record a state baseline immediately before the agent acts. After the agent acts, measure the state again. The verification criteria must assert only on the mathematically or logically computed *delta* between the post-state and the pre-state.

If the agent is supposed to create a new user, assert `user_count_post - user_count_pre == 1`.
If the agent is supposed to append a log line, assert `len(log_lines_post) - len(log_lines_pre) == 1`.

## Mechanism

1. **Pre-Hook (Baseline Capture):** Query the specific environment metric before handing control to the agent.
2. **Context Passing:** Store the baseline alongside the current execution trajectory and treat it as immutable once captured.
3. **Agent Execution:** The agent performs its task.
4. **Post-Hook (Measurement):** Query the exact same environment metric.
5. **Delta Calculation:** Subtract, diff, or otherwise compare the two states, and assert on the diff.

## Pattern / Antipattern

The same task: verify that an agent created one new flow in a shared environment.

### Antipattern: absolute assertion

The naive implementation checks the final count only. It can pass before the agent does anything.

```python
def verify_flow_created_naive(get_flow_count):
    observed = get_flow_count()
    return {
        "passed": observed >= 1,
        "observed": observed,
        "expected": "at least 1 flow",
    }
```

### Pattern: baseline plus delta assertion

The structured implementation captures the baseline before the agent acts and verifies the change measured during this run's verification window.

```python
from typing import Callable


class DeltaVerifier:
    def __init__(self, metric_name: str, fetch_state_fn: Callable[[], int], expected_delta: int):
        self.metric_name = metric_name
        self.fetch_state_fn = fetch_state_fn
        self.expected_delta = expected_delta
        self.pre_state = None
        self.post_state = None

    def capture_baseline(self) -> int:
        """Called by the orchestrator before the agent acts."""
        self.pre_state = self.fetch_state_fn()
        return self.pre_state

    def verify_delta(self) -> dict:
        """Called by the verifier after the agent acts."""
        if self.pre_state is None:
            raise ValueError("baseline never captured; cannot verify a delta")
        self.post_state = self.fetch_state_fn()
        actual_delta = self.post_state - self.pre_state
        return {
            "check": f"{self.metric_name}_delta",
            "metric": self.metric_name,
            "passed": actual_delta == self.expected_delta,
            "expected_delta": self.expected_delta,
            "actual_delta": actual_delta,
            "pre_state": self.pre_state,
            "post_state": self.post_state,
        }


# A shared environment that already holds unrelated flows before the agent runs.
flows = [{"id": 1}, {"id": 2}, {"id": 3}]


def get_flow_count() -> int:
    return len(flows)


def verify_flow_created_naive_local(get_flow_count: Callable[[], int]) -> dict:
    observed = get_flow_count()
    return {
        "passed": observed >= 1,
        "observed": observed,
        "expected": "at least 1 flow",
    }


flow_verifier = DeltaVerifier("active_flows", get_flow_count, expected_delta=1)
flow_verifier.capture_baseline()       # pre-action: records 3
assert verify_flow_created_naive_local(get_flow_count)["passed"] is True
flows.append({"id": 4})                # the agent creates exactly one flow this run
report = flow_verifier.verify_delta()  # post-action check

assert report == {
    "check": "active_flows_delta",
    "metric": "active_flows",
    "passed": True,
    "expected_delta": 1,
    "actual_delta": 1,
    "pre_state": 3,
    "post_state": 4,
}
assert report["pre_state"] == 3 and report["post_state"] == 4
assert report["passed"]                     # the measured change in this window is +1
```

Aider's command tests show this shape in a real suite: they capture `initial_count = len(coder.abs_fnames)` before dropping files from a chat session, then after the drop assert that membership changed and `len(coder.abs_fnames) == initial_count - 1`. The check is on the relative file-set change, not an absolute count, so it holds no matter how many files were already in the session.

## Determinism Move

Delta constrains `ambient_state` by turning an absolute assertion into a relative assertion scoped to the current run. The baseline and post-state expose whether the matching object was already present before the agent acted. The determinism move is scoping the assertion to a captured baseline, so a pass means the measured state changed by the expected amount during this run's verification window. Full causal attribution under concurrent activity requires scoped metrics, exclusive access, or pairing with **Causal Tag**.

## Observable Signal

The observable signal reports the baseline, the new state, the computed delta, the expectation, and the metric being measured.

Every report should include:

* the baseline value captured before the agent acted;
* the post-action value captured after the agent acted;
* the computed delta;
* the expected delta;
* the named metric used for both captures.

```text
check: active_flows_delta
metric: active_flows
passed: true
pre_state: 3
post_state: 4
expected_delta: 1
actual_delta: 1
```

## Failure Modes

* **Concurrency Contamination:** If other agents or users are modifying the environment at the exact same time, the delta might be +2 instead of +1. Mitigation: combine Delta with **Causal Tag**, tagging the agent's specific artifacts with a UUID.
* **Stale Baselines:** Capturing the baseline too early (e.g., at system boot instead of immediately before the specific step being verified).

## Use When

Use this pattern when:

* the environment is shared, persistent, or carries non-trivial pre-existing state;
* the metric being measured exists in the environment before the agent acts;
* concurrent activity is possible and the metric can be scoped, locked, or paired with Causal Tag;
* the assertion needs to prove the state changed during the agent's verification window, with causal attribution handled by scoping, exclusive access, or Causal Tag when concurrency is present.

## Do Not Use When

Do not reach for Delta when:

* the environment is fully ephemeral (fresh container per run, mocked DB);
* the metric does not exist pre-action and only the absolute post-state is meaningful;
* you cannot capture a baseline before the agent acts (e.g., the agent is invoked black-box);
* the action is destructive or non-replayable and a pre-state read would alter the outcome.

In those cases, absolute assertions or Causal Tag are simpler and more honest.

## Evidence

* **[Aider](https://github.com/Aider-AI/aider) command tests:** the delta sweep records a direct instance in aider's `test_commands.py`: the drop-file tests capture `initial_count = len(coder.abs_fnames)` and then assert `len(coder.abs_fnames) == initial_count - 1`, a relative file-set delta rather than an absolute count.
* **Test Flakiness Analysis:** Luo et al. identify state contamination and order dependence as recurring causes of flaky tests in software engineering (Luo et al., FSE 2014).
* **Verification Design Principles (Principle 9):** "Assertions must prove the system's actions caused the expected outcome, not that the environment happened to already contain matching data."

## Related Patterns

* **State Baseline:** the Context pattern that captures and carries the pre-state Delta asserts on.
* **Causal Tag:** complementary for shared or concurrent environments; tag the agent's artifacts so a +2 from another actor does not mislead the delta.
* **Comparator:** Delta is one named comparison operator (relative change) in the broader operator family.
* **Executable Analog:** a delta assertion is the executable check for a state-change claim.
* **Backpressure:** a failed delta check is a concrete failure signal that can drive a bounded rerun.
