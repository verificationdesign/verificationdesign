# State Baseline

*(Context Pattern)*

## Name

**State Baseline**

Also known as: Pre-Action Snapshot, Baseline Capture, Snapshot-Restore Harness.

## Intent

Capture the relevant environment or process state before an action under verification, so the verifier can prove the action caused the observed change instead of accepting state that already existed.

## Problem

Agentic systems act inside shared state: filesystems, global registries, environment variables, databases, queues, browser sessions, and cloud accounts. A verifier that only looks at post-action state cannot tell whether the agent caused the state or merely found it.

For example, if an agent is supposed to delete a file, a post-action check like `assert not path.exists()` passes when the file was already absent. If an agent is supposed to register a hook, `assert len(hooks) == 1` passes when a previous test leaked one hook into the registry. The check is green, but it has not verified the action.

This is ordinary state contamination, but LLM agents make it easier to miss. A deterministic test usually fails later when inherited state conflicts with another assertion. An agent can rationalize the coincidental pass and continue the run as if it proved success. `verification_design.md` Principle 9 names this explicitly: assertions must prove the system's action caused the expected outcome, not that the environment happened to contain matching data. Luo et al. identify state leakage and order dependence as recurring sources of flaky tests in software systems (FSE 2014).

Without a baseline, verification cannot separate causality from coincidence.

## Forces

* **Shared environments vs. fresh environments.** A fresh container or mocked database avoids inherited state, but many useful checks run against persistent workspaces or live services.
* **Snapshot scope vs. snapshot cost.** Capturing every file, row, or variable can be expensive; capturing too little leaves hidden state surfaces.
* **Per-action vs. per-session baselines.** A session-level snapshot can support rollback, but a verifier often needs a baseline immediately before a specific action.
* **Comparison vs. cleanup.** Some baselines exist to compute a Delta; others exist to restore state after the action.
* **Local mutation vs. audit trail.** Direct mutation is simple, but destructive operations need a preimage if they are part of a verification loop.

## Solution

Snapshot the relevant state surface before the agent acts. After the action, either compare post-state to the baseline or restore the baseline during cleanup.

The baseline must be close enough to the action to answer the verifier's actual question: "what changed during this step?" A startup snapshot may be useful for session recovery, but it does not prove a particular action caused a particular post-condition.

Common shapes:

* **In-memory snapshot:** copy global lists, registries, caches, or settings before the test, then restore them after.
* **File-backed inventory:** write a named list of files, resources, plugin IDs, or API objects, then compare the current inventory to that baseline.
* **Process-environment snapshot:** capture environment variables and redirect state directories to a temporary location, then restore in `finally`.
* **Snapshot-replay:** persist enough runtime state to reconstruct an event stream or resume from a pause boundary.
* **Git preimage:** commit or hash original files before an automated edit, then compare or restore from that preimage.

State Baseline is often paired with **Delta**. State Baseline supplies the pre-state. Delta computes the change.

## Mechanism

1. **Identify the state surface.** Name the files, registry, environment variables, database rows, queue messages, or runtime objects that could satisfy the assertion by accident.
2. **Capture pre-state.** Snapshot that state immediately before the action under verification, using the narrowest mechanism that covers the risk.
3. **Run the action.** Hand control to the agent, tool, workflow, or test body.
4. **Measure or restore.** Either capture post-state for comparison or restore the pre-state during cleanup.
5. **Report the baseline.** Record the snapshot mechanism, baseline value or reference, post-action value, and cleanup status.

## Pattern / Antipattern

Both examples show the same State Baseline move on different state surfaces. The antipattern mutates workspace files with no nearby preimage. The pattern snapshots an in-memory registry, clears inherited state for the action, and restores the original registry afterward.

### Antipattern: mutate shared state with no preimage

This shape is not wrong in every production path. It becomes a verification antipattern when an agent-facing operation can alter shared state and the surrounding harness has no nearby baseline, restore point, or diff check.

```python
from pathlib import Path


class WorkspaceFiles:
    def __init__(self, root: Path):
        self.root = root

    def move(self, source: str, destination: str) -> None:
        source_path = self.root / source
        destination_path = self.root / destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(destination_path)

    def delete(self, path: str) -> None:
        target = self.root / path
        target.unlink()
```

If a verifier later checks only `not source_path.exists()` or `destination_path.exists()`, it cannot prove this operation caused that post-state. The file may have already been absent, already moved, or modified by another actor. The verifier has no preimage to inspect.

AutoGPT's file manager evidence has this shape: append, move, and delete mutate workspace files directly, while `save_state` exists as an explicit session operation rather than a per-action baseline. Treat it as a partial-fit antipattern because direct mutation is legitimate outside a verification seam; the risk appears when an agent loop treats post-state as proof without a nearby snapshot.

### Pattern: snapshot, isolate, restore

The structured implementation captures the original registry, clears inherited state, yields to the action, and restores the exact pre-state afterward.

```python
from contextlib import contextmanager


before_hooks = []
after_hooks = []
error_hooks = []


def hook_counts():
    return [len(before_hooks), len(after_hooks), len(error_hooks)]


def report(pre_state, post_state):
    return {
        "check": "hooks.registry.isolated",
        "snapshot": "in_memory",
        "covered": ["before_hooks", "after_hooks", "error_hooks"],
        "pre_state": pre_state,
        "post_state": post_state,
        "cleanup": "restored",
    }


@contextmanager
def isolated_hooks():
    # 1. Capture the pre-state.
    baseline = (list(before_hooks), list(after_hooks), list(error_hooks))

    # 2. Remove inherited state for this test.
    before_hooks.clear()
    after_hooks.clear()
    error_hooks.clear()

    try:
        # 3. Run the action under verification.
        yield
    finally:
        # 4. Restore the pre-state even if the test fails.
        before_hooks.clear()
        after_hooks.clear()
        error_hooks.clear()
        before_hooks.extend(baseline[0])
        after_hooks.extend(baseline[1])
        error_hooks.extend(baseline[2])


before_hooks.append("inherited")
captured_baseline = (list(before_hooks), list(after_hooks), list(error_hooks))

with isolated_hooks():
    after_hooks.append("registered")
    isolated_state = hook_counts()
    assert "inherited" not in before_hooks and after_hooks == ["registered"]

assert (before_hooks, after_hooks, error_hooks) == captured_baseline

baseline_report = report(
    pre_state=[len(hooks) for hooks in captured_baseline],
    post_state=isolated_state,
)
assert baseline_report == {
    "check": "hooks.registry.isolated",
    "snapshot": "in_memory",
    "covered": ["before_hooks", "after_hooks", "error_hooks"],
    "pre_state": [1, 0, 0],
    "post_state": [0, 1, 0],
    "cleanup": "restored",
}
```

The verifier can now reason about state inside the test body without inheriting previous runs. CrewAI's hook tests use this in-memory snapshot-and-restore shape around global hook lists. Other sourced variants use a file-backed inventory, a temporary home directory with environment restore, workflow event snapshots, and owned-resource ledgers.

## Determinism Move

State Baseline constrains `ambient_state` by recording the state the agent did not create. Restoring the baseline after the action closes the same source of error: one run's residue should not become the next run's setup.

The move is simple: make inherited state observable before the agent acts. Once pre-state is explicit, a verifier can compute Delta, restore cleanup state, or reject a post-condition that was already true.

## Observable Signal

Every State Baseline report should include:

* `check`: the verifier or registry check being protected;
* `snapshot`: the snapshot mechanism (`in_memory`, `file_backed`, `process_env`, `snapshot_replay`, `git_preimage`);
* `covered`: the state surfaces covered by the baseline;
* `pre_state`: the pre-action value or snapshot reference;
* `post_state`: the post-action value when comparison is used;
* `cleanup`: the cleanup status (`restored`, `leaked`, `partial`, `not_applicable`).

The most useful report is boring and concrete:

```text
check: hooks.registry.isolated
snapshot: in_memory
covered: ["before_hooks", "after_hooks", "error_hooks"]
pre_state: [1, 0, 0]
post_state: [0, 1, 0]
cleanup: restored
```

## Failure Modes

* **Stale Baseline:** The snapshot is captured too early, such as at process start, while the action is verified much later. Capture baselines in the narrowest scope possible.
* **Snapshot Leak:** The test fails before cleanup and leaves modified state behind. Use `try/finally`, pytest yield fixtures, or equivalent cleanup mechanisms.
* **Partial Snapshot:** The harness captures one state surface but misses another. Enumerate coverage in the report and fail when a required surface is uncovered.
* **Baseline Without Version:** A stored baseline file drifts silently. Version baseline files and require explicit migration notes when the expected inventory changes.

## Use When

Use this pattern when:

* the environment is shared, persistent, or reused across runs;
* a pre-existing object could satisfy the post-condition;
* concurrent activity can create, delete, or mutate matching state;
* the action is destructive and needs an audit trail;
* the verifier needs to prove causation, not merely observe a final condition.

## Do Not Use When

Do not reach for State Baseline when:

* the environment is fully ephemeral and recreated for each run;
* the state surface is too large and the assertion is low stakes;
* the verified property is purely internal to a deterministic function call;
* a **Causal Tag** can identify the agent's own artifacts more directly;
* a pre-state read would itself change the system under test.

## Evidence

* **Verification Design Principle 9:** The canonical design doc states that verification must prove the agent's action caused the outcome, not that ambient state already matched. It cites Luo et al. on state contamination in flaky tests (FSE 2014).
* **[CrewAI](https://github.com/crewAIInc/crewAI) hook fixture:** The evidence summary records a direct State Baseline pattern: global hook registries are copied, cleared, yielded to the test, then restored.
* **[OpenClaw](https://github.com/openclaw/openclaw) and [Dify](https://github.com/langgenius/dify) variants:** The evidence summary records file-backed inventory, process-environment snapshot, and workflow snapshot-replay variants.
* **[AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) file manager:** The antipattern cleanup sweep records direct append, move, and delete operations on workspace files without a nearby per-action preimage. The note treats this as moderate evidence because direct mutation is only the failure when used as a verification seam.

## Related Patterns

* **Delta:** uses the baseline to compute what changed during this run.
* **Causal Tag:** tags artifacts when snapshotting shared state is too expensive or ambiguous.
* **Constitution:** can require baseline capture as part of the criteria contract.
* **Trajectory Cursor:** tracks position and state inside a multi-step process.
* **Executable Analog:** turns the snapshot or restore check into a runnable verifier.
