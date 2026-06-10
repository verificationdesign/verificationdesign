# Trajectory Cursor

*(Context Pattern)*

## Name

**Trajectory Cursor**

Also known as: Action History Cursor, Step Cursor, Trajectory Record, Execution Cursor.

## Intent

Maintain an explicit, structured record of where the agent is in its multi-step process and what happened at each boundary, so the verifier and the next turn can read the trajectory instead of inferring it from chat history or model recall.

## Problem

Agents do not fail only by choosing a bad action. They also fail by losing track of what happened.

In a multi-step loop, the model may propose an action, a policy layer may deny it, a tool may error, a retry may run, or a fallback may skip the intended path. If that boundary is not recorded in the trajectory, the next turn reconstructs the past from chat text and latent memory. The missing event becomes invisible. The agent may propose the same denied command again, skip the action that mattered, or claim progress that never occurred.

The verifier has the same problem. A final answer may look plausible, but without a cursor the verifier cannot tell which tool calls actually happened, which errors were recovered, which denials were seen by the next turn, or whether the loop made forward progress.

`verification_design.md` Principle 3 frames tool-agent verification as a step-level problem. Its ToolPRMBench update points toward checking tool choice, arguments, and observed tool-state transitions at each action boundary, using interaction history rather than final task success alone (arXiv:2601.12294). Trajectory Cursor is the context pattern that makes that interaction history explicit.

## Forces

* **Model recall vs. explicit record.** Chat history contains the story, but a cursor records the state machine the verifier can inspect.
* **Cursor granularity.** Some systems need one entry per tool call; others need per-step, per-task, or per-graph-node state.
* **Forward-only vs. resumable.** A short loop may only need append-only history; a workflow engine may need persisted cursor state for pause and resume.
* **Audit log vs. control signal.** A passive transcript helps later review, but a cursor should also guide the next action.
* **Cursor maintenance cost vs. loop failure cost.** Recording each boundary adds bookkeeping; missing one denial can create an infinite retry loop.

## Solution

Define a structured trajectory schema and append one entry at every observable boundary: proposal, decision, execution, denial, result, and feedback.

Before the agent composes its next action, read the cursor as the source of truth. Do not ask the model to infer what happened from prose. Do not let failure paths return bare errors that never enter history. If a permission check denies an action, the denial is an entry. If a retry happens, the retry is an entry. If a tool result is missing, the missing result is visible as a gap.

Common shapes:

* **Action-history list:** entries record tool name, arguments, decision, outcome, error, denial reason, and feedback. This is the canonical shape for single-agent loops.
* **Step counter with status:** planned, executed, denied, skipped, errored. This is enough when the action graph is fixed.
* **Resumable snapshot:** persisted cursor state lets a workflow pause, replay a prefix, and resume. Dify's workflow event snapshot evidence fits this variant.
* **Graph execution cursor:** per-task or per-node execution state separates reusable agent objects from the graph's current execution position. AutoGen GraphFlow tests are the canonical pattern evidence here.

The cursor is not just a log. A log can be written after the fact. A cursor is consumed by the next turn and by the verifier.

## Mechanism

1. **Define the schema.** Name valid entry types such as proposal, decision, execution, denial, result, and feedback.
2. **Append before yielding.** Every boundary appends a structured entry before control returns to the next turn or node.
3. **Read before proposing.** The next action is conditioned on the recorded trajectory, not on model recall.
4. **Verify forward progress.** Detect repeated proposals, missing critical actions, unrecorded boundaries, and stalled cursor positions.
5. **Report cursor state.** Record the last cursor position, the entry that advanced it, and any progress checks the verifier ran.

## Pattern / Antipattern

The two examples show the same cursor move at different boundary types: the antipattern loses a denial outside the trajectory, while the pattern records each graph-node boundary on the observed outcome that advanced it.

### Antipattern: denial outside the trajectory

The naive implementation checks permission, receives a denial, returns a bare error, and leaves action history unchanged. The next turn cannot see the denial and may propose the same command again.

```python
class AgentLoop:
    def __init__(self, model, permission_manager):
        self.model = model
        self.permission_manager = permission_manager
        self.action_history = []

    def run_turn(self, task):
        proposal = self.model.propose(task, history=self.action_history)
        decision = self.permission_manager.check(proposal)

        if not decision.allowed:
            return {
                "status": "error",
                "message": "Permission denied",
            }

        result = proposal.execute()
        self.action_history.append({
            "type": "result",
            "tool": proposal.tool_name,
            "args": proposal.args,
            "result": result,
        })
        return result
```

The denial is real, but the cursor never sees it. The model receives the same `action_history` on the next turn and can re-propose the same denied action.

AutoGPT's permission-denial regression test names this exact failure: a denied command returned an error without feedback in action history, so the agent had no memory of the denial and proposed the same command again. The fix was to register the denial as feedback through `do_not_execute`, making the boundary visible to the next prompt.

AutoGPT's benchmark analyzer shows the same class at population scale: repeated same-tool loops, missing critical actions such as `write_file`, timeouts, and unrecovered errors are trajectory-level failures, not merely bad final answers.

### Pattern: cursor advances at every boundary

The structured implementation records the graph execution cursor and verifies that each task advances through the expected path.

```python
class EchoAgent:
    def __init__(self, name):
        self.name = name

    def run(self, task):
        return f"{self.name}:{task}"


class GraphCursor:
    def __init__(self, nodes):
        self.nodes = nodes
        self.entries = []

    def run_task(self, task):
        task_id = len({entry["task_id"] for entry in self.entries}) + 1
        self.entries.append({
            "type": "proposal",
            "task_id": task_id,
            "content": task,
        })

        for node in self.nodes:
            outcome = node.run(task)
            self.entries.append({
                "type": "execution",
                "task_id": task_id,
                "node": node.name,
                "outcome": outcome,
            })

        return [entry for entry in self.entries if entry["task_id"] == task_id]

    def report(self, task_id):
        entries = [entry for entry in self.entries if entry["task_id"] == task_id]
        executions = [entry for entry in entries if entry["type"] == "execution"]
        expected_nodes = [node.name for node in self.nodes]
        recorded_nodes = [entry["node"] for entry in executions]
        missing_nodes = [node for node in expected_nodes if node not in recorded_nodes]
        repeat_count = sum(
            1
            for previous, current in zip(recorded_nodes, recorded_nodes[1:])
            if previous == current
        )
        last_entry = executions[-1]

        return {
            "cursor": f"graph.task.{task_id}",
            "last_entry": f"execution(node={last_entry['node']}, task_id={task_id})",
            "path": " -> ".join(recorded_nodes),
            "repeat_loop_count": repeat_count,
            "missing_required_actions": missing_nodes,
            "unrecorded_boundaries": len(expected_nodes) - len(executions),
        }


agents = [EchoAgent("A"), EchoAgent("B"), EchoAgent("C")]
cursor = GraphCursor(nodes=agents)

first = cursor.run_task("First task")
second = cursor.run_task("Second task")

assert [entry["node"] for entry in first if entry["type"] == "execution"] == ["A", "B", "C"]
assert [entry["outcome"] for entry in second if entry["type"] == "execution"] == [
    "A:Second task",
    "B:Second task",
    "C:Second task",
]
assert {entry["task_id"] for entry in first}.isdisjoint(
    {entry["task_id"] for entry in second}
)

assert cursor.report(2) == {
    "cursor": "graph.task.2",
    "last_entry": "execution(node=C, task_id=2)",
    "path": "A -> B -> C",
    "repeat_loop_count": 0,
    "missing_required_actions": [],
    "unrecorded_boundaries": 0,
}
```

AutoGen's GraphFlow test has this shape: the same graph runs two sequential tasks, each result contains the expected user, A, B, C message path, and each agent's message counter increments once per task. The cursor is the graph's per-task execution position, not the agent objects themselves.

Dify's workflow event snapshot service is a resumable variant: persisted workflow state can reconstruct an event prefix before live execution continues. AutoGen's C# termination tests are supporting evidence for the reset shape, but the Python GraphFlow test is the canonical card instance.

## Determinism Move

Trajectory Cursor constrains `context_contamination` by making the trajectory an explicit record the next turn reads instead of reconstructing from chat memory. It constrains `tool_boundary_ambiguity` by requiring every observable boundary to produce a structured entry.

The determinism move is boundary accounting. A proposal, denial, execution, result, retry, and feedback event are different states. If the cursor records them, the next turn and verifier can distinguish them. If not, the model is left to guess what happened.

## Observable Signal

Every Trajectory Cursor report should include:

* `cursor`: the last cursor position;
* `last_entry`: the entry that advanced the cursor most recently;
* `path`: the recorded path for the task;
* `repeat_loop_count`: repeated adjacent entries in the recorded path;
* `missing_required_actions`: expected actions absent from the recorded path;
* `unrecorded_boundaries`: expected boundaries with no execution entry.

The most useful report shows forward progress directly:

```text
cursor: graph.task.2
last_entry: execution(node=C, task_id=2)
path: A -> B -> C
repeat_loop_count: 0
missing_required_actions: []
unrecorded_boundaries: 0
```

## Failure Modes

* **Repeat-Loop:** The agent repeats an action because the previous success, denial, or error is not visible to the next turn. Append the outcome before dispatching the next turn.
* **Missing Critical Action:** The cursor advances without invoking the action required to satisfy the task. Track required actions and assert that each appears in the trajectory.
* **Unrecorded Boundary:** Permission denials, retries, fallbacks, or tool errors occur outside the cursor. Require every boundary, including failure paths, to emit an entry.
* **Cursor Drift:** The cursor advances because the model says progress happened, but no execution entry records the completed step. Advance only on observable outcomes.

## Use When

Use this pattern when:

* an agent runs more than two tool calls per task;
* permission, retry, fallback, or denial paths exist outside the main action flow;
* verification needs to prove which steps executed, not which the agent narrated;
* a loop can stall, repeat, or skip required actions;
* pause, replay, or human-in-the-loop resume matters.

## Do Not Use When

Do not reach for Trajectory Cursor when:

* the workflow is a single-shot model call with no loop;
* the framework already persists a structured trajectory and another cursor would duplicate state;
* the process is a deterministic transformation pipeline with no agent decisions;
* the only verification question is final-state causality, where **State Baseline** or **Delta** is enough.

## Evidence

* **Verification Design Principle 3:** The design doc's ToolPRMBench update frames tool-agent verification around interaction history and action-boundary checks, not only final success (arXiv:2601.12294).
* **[AutoGen](https://github.com/microsoft/autogen) GraphFlow:** The evidence summary records a Python GraphFlow test where the same graph runs two sequential tasks, each task follows the expected A, B, C path, and agent counters show one execution per task.
* **[Dify](https://github.com/langgenius/dify) workflow snapshots:** The evidence summary records a resumable cursor variant where workflow events are reconstructed from persisted snapshots.
* **[AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) permission-denial regression:** The antipattern cleanup sweep records a denied action that was not registered in history, causing repeat proposals until the denial was added as feedback.
* **AutoGPT benchmark analyzer:** The same sweep records trajectory-level failure categories: repeated same-tool loops, missing critical actions, timeouts, and unrecovered errors.

## Related Patterns

* **State Baseline:** snapshots environment state; Trajectory Cursor snapshots the agent's action history.
* **Delta:** forward progress is a Delta on cursor position.
* **Causal Tag:** links cursor entries to external artifacts the agent created.
* **Executable Analog:** repeat-loop and missing-action checks are executable checks over the cursor.
* **Constitution:** can encode required actions and cursor schema as verification criteria.
