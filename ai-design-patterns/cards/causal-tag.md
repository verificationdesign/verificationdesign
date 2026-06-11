# Causal Tag

*(Context Pattern)*

## Name

**Causal Tag**

Also known as: Causal ID, Run ID Propagation, Invocation Tag, Event Parentage.

## Intent

Stamp every event the agent emits with a stable joinable identifier and, when applicable, a parent identifier, so verification can attribute observed effects to specific agent actions rather than inferring causality from temporal proximity in shared ambient state.

## Problem

Agents often act into shared event surfaces: logs, traces, message buses, third-party APIs, file stores, and callback systems. A verifier looking at that surface has to answer a causality question:

Did this agent cause the observed effect, or did something similar happen nearby?

Without causal tags, attribution usually falls back to a time window:

* capture `start_time`;
* trigger the agent;
* count matching log entries after `start_time`;
* pass if the count is high enough.

That is weaker than it looks. Any producer that emits a matching event after the timestamp can satisfy the assertion. The verifier has a time baseline, but no identity. This is the same ambient-state problem as **State Baseline** and **Delta**, but the failure surface is distributed and asynchronous.

`verification_design.md` Principle 9 says assertions must prove the system's action caused the expected outcome, not that the environment happened to contain matching data. Causal Tag is the identity-based answer: make the agent's own effects queryable.

## Forces

* **Framework tracing vs. custom tagging.** Many frameworks already expose run IDs, invocation IDs, or callback parentage. Bypassing that layer creates unnecessary attribution debt.
* **Time-window attribution vs. identity attribution.** Timestamps narrow the search space; fresh, run-scoped IDs support attribution when the verifier requires that ID on the observed effect.
* **Flat ID vs. tree.** A single run ID groups events. A parent ID reconstructs causality across nested model, tool, retriever, and guardrail calls.
* **Generated IDs vs. supplied IDs.** Framework-generated IDs reduce caller burden; caller-supplied IDs help join to external payloads.
* **Propagation cost vs. audit cost.** Carrying IDs through each boundary adds plumbing, but missing IDs make failures expensive to investigate.

## Solution

Tag every event the agent emits with a stable identifier. When events form a causal chain, record the parent identifier too. Use the framework tracing layer if one exists; do not invent a parallel ID system unless the framework has none.

The pattern lives at three layers:

* **Framework callback signature:** model, tool, and retriever callbacks receive `run_id` and optional `parent_run_id`. LangChain's callback tree is the canonical shape.
* **Invocation-scoped context:** a context object owns a stable invocation ID; session events inherit it; each event also gets its own ID. ADK's `InvocationContext` and `Event.id` are the canonical variant.
* **Domain payload:** outbound side effects carry the tag into the external surface: message attributes, HTTP headers, log fields, third-party metadata, or filenames.

Framework integration is half the pattern. The other half is propagation into the surface the verifier actually reads. A `run_id` trapped inside an in-memory trace store does not help a verifier filtering Cloud Run logs unless the same ID appears in those logs.

## Mechanism

1. **Identify the tracing layer.** Use callback tree, invocation context, or event store. If none exists, create a small context object with a stable ID at run entry.
2. **Use IDs at every boundary.** Model calls, tool calls, retriever calls, guardrail interventions, and outbound side effects all carry the run or invocation ID.
3. **Preserve parent links.** Child events record the parent run or event ID so the tree can be reconstructed.
4. **Stamp emitted artifacts.** Logs, message payloads, API calls, and trace records include the tag in a queryable field.
5. **Verify the tree and destination join.** The report includes ID generation policy, tag propagation, and parent consistency, then joins tags read from the destination surface back to the source action. Orphan events are failures.

## Pattern / Antipattern

The same task: verify that a triggered event reached a downstream handler. The antipattern filters shared logs by path and timestamp. The pattern tags the causal chain and verifies events by identity.

### Antipattern: path plus timestamp count

The naive implementation captures a time baseline and counts matching log entries after that time. It has partial Delta machinery, but no causal identity.

```python
from datetime import datetime, timezone


def count_matching_log_entries(logs, path: str, start_time: datetime) -> int:
    return sum(
        1 for entry in logs
        if entry.path == path
        and entry.status == 200
        and entry.timestamp >= start_time
    )


def test_trigger_reaches_handler(pubsub, logs):
    start_time = datetime.now(timezone.utc)
    pubsub.publish("hello-pipeline-test")

    count = count_matching_log_entries(
        logs,
        path="/apps/trigger_echo_agent/trigger/pubsub",
        start_time=start_time,
    )

    assert count >= 1
```

Any matching request after `start_time` satisfies this test. The event may have come from this publish, another test, a retry, a manual request, or ambient traffic.

ADK's remote trigger tests have this shape: they publish Pub/Sub or Eventarc messages, then count Cloud Run log entries filtered by request path, status, and timestamp. The test captures a time baseline, so this is not a total absence of verification structure. The missing piece is identity. A unique test-run ID or message ID should be carried in the payload and required in the observed log entry.

### Pattern: run ID tree with parent links

The structured implementation records every event with a run ID and parent run ID, carries the tag into the shared destination log, then verifies the destination entry by identity.

```python
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TracedEvent:
    run_id: UUID
    parent_run_id: UUID | None
    kind: str
    payload: dict


class Tracer:
    def __init__(self):
        self.events: list[TracedEvent] = []

    def start(
        self,
        kind: str,
        parent_run_id: UUID | None = None,
        run_id: UUID | None = None,
        **payload,
    ) -> UUID:
        run_id = run_id or uuid4()
        self.events.append(
            TracedEvent(
                run_id=run_id,
                parent_run_id=parent_run_id,
                kind=f"{kind}.start",
                payload=payload,
            )
        )
        return run_id

    def emit(self, run_id: UUID, kind: str, **payload) -> None:
        parent = self.parent_of(run_id)
        self.events.append(
            TracedEvent(
                run_id=run_id,
                parent_run_id=parent,
                kind=kind,
                payload=payload,
            )
        )

    def parent_of(self, run_id: UUID) -> UUID | None:
        for event in self.events:
            if event.run_id == run_id:
                return event.parent_run_id
        raise KeyError(f"Unknown run id: {run_id}")

    def path_to_root(self, run_id: UUID) -> list[UUID]:
        path = [run_id]
        parent = self.parent_of(run_id)
        while parent is not None:
            path.append(parent)
            parent = self.parent_of(parent)
        return path

    def check_tree(self) -> dict[str, int | bool]:
        known_ids = {event.run_id for event in self.events}
        parents_by_run: dict[UUID, set[UUID | None]] = {}
        orphan_events = 0
        root_parent_errors = 0

        for event in self.events:
            parents_by_run.setdefault(event.run_id, set()).add(event.parent_run_id)
            if event.parent_run_id is not None and event.parent_run_id not in known_ids:
                orphan_events += 1
            if event.kind == "agent.start" and event.parent_run_id is not None:
                root_parent_errors += 1

        parent_conflicts = sum(
            1 for parents in parents_by_run.values() if len(parents) > 1
        )
        return {
            "consistent": (
                orphan_events == 0
                and parent_conflicts == 0
                and root_parent_errors == 0
            ),
            "orphan_events": orphan_events,
            "parent_conflicts": parent_conflicts,
            "root_parent_errors": root_parent_errors,
        }


def write_handler_log(
    tracer: Tracer,
    destination_log: list[dict],
    run_id: UUID,
    path: str,
    *,
    propagate_tag: bool,
) -> dict:
    payload = {"source": "agent"}
    if propagate_tag:
        payload["causal_tag"] = str(run_id)
    else:
        payload["expected_causal_tag"] = str(run_id)

    entry = {
        "path": path,
        "status": 200,
        "payload": payload,
    }
    destination_log.append(entry)
    if propagate_tag:
        tracer.emit(
            run_id,
            "handler.received",
            surface="shared_log",
            causal_tag=str(run_id),
        )
    return entry


def count_by_path_and_status(destination_log: list[dict], path: str) -> int:
    return sum(
        1 for entry in destination_log
        if entry["path"] == path and entry["status"] == 200
    )


def query_by_causal_tag(destination_log: list[dict], run_id: UUID) -> list[dict]:
    return [
        entry for entry in destination_log
        if entry["payload"].get("causal_tag") == str(run_id)
    ]


def count_missing_destination_tags(destination_log: list[dict]) -> int:
    return sum(
        1 for entry in destination_log
        if "expected_causal_tag" in entry["payload"]
        and "causal_tag" not in entry["payload"]
    )


def short(run_id: UUID | None) -> str:
    return "null" if run_id is None else run_id.hex[-4:]


def render_report(
    tracer: Tracer,
    root_id: UUID,
    *,
    destination_tag_missing: int,
    id_generation_policy: str,
) -> str:
    tree = tracer.check_tree()
    lines = [f"root_run_id: {short(root_id)}"]
    for event in tracer.events:
        surfaces = ["trace_store"]
        if event.payload.get("causal_tag") == str(event.run_id):
            surfaces.append("shared_log_payload")
        lines.append(
            "event: "
            f"{event.kind} run: {short(event.run_id)} "
            f"parent: {short(event.parent_run_id)} "
            f"tag_present: {', '.join(surfaces)}"
        )
    lines.extend(
        [
            "propagation_surfaces_checked: trace_store, shared_log_payload",
            "destination_tag_observed: shared_log_payload",
            f"tree_consistency: {'pass' if tree['consistent'] else 'fail'}",
            f"orphan_events: {tree['orphan_events']}",
            f"destination_tag_missing: {destination_tag_missing}",
            f"id_generation_policy: {id_generation_policy}",
        ]
    )
    return "\n".join(lines)


tracer = Tracer()
root_id = tracer.start(
    "agent",
    run_id=UUID("00000000-0000-0000-0000-00000000a001"),
    prompt="answer user",
)
tool_id = tracer.start(
    "tool",
    parent_run_id=root_id,
    run_id=UUID("00000000-0000-0000-0000-00000000b002"),
    name="web_fetch",
)
path = "/apps/trigger_echo_agent/trigger/pubsub"
destination_log = [
    {
        "path": path,
        "status": 200,
        "payload": {"source": "ambient"},
    }
]

agent_entry = write_handler_log(
    tracer, destination_log, tool_id, path, propagate_tag=True
)
dropped_tag_entry = write_handler_log(
    tracer, destination_log, tool_id, path, propagate_tag=False
)
selected = query_by_causal_tag(destination_log, tool_id)

assert count_by_path_and_status(destination_log, path) > 1
assert selected == [agent_entry]
assert agent_entry["payload"]["causal_tag"] == str(tool_id)
assert "causal_tag" not in destination_log[0]["payload"]
assert dropped_tag_entry not in selected
assert count_missing_destination_tags(destination_log) == 1
assert tracer.check_tree() == {
    "consistent": True,
    "orphan_events": 0,
    "parent_conflicts": 0,
    "root_parent_errors": 0,
}

events_with_orphan = list(tracer.events)
events_with_orphan.append(
    TracedEvent(
        run_id=UUID("00000000-0000-0000-0000-00000000c003"),
        parent_run_id=UUID("00000000-0000-0000-0000-00000000d004"),
        kind="tool.start",
        payload={},
    )
)
orphan_demo = Tracer()
orphan_demo.events = events_with_orphan
assert orphan_demo.check_tree()["consistent"] is False
assert orphan_demo.check_tree()["orphan_events"] == 1

expected_report = """root_run_id: a001
event: agent.start run: a001 parent: null tag_present: trace_store
event: tool.start run: b002 parent: a001 tag_present: trace_store
event: handler.received run: b002 parent: a001 tag_present: trace_store, shared_log_payload
propagation_surfaces_checked: trace_store, shared_log_payload
destination_tag_observed: shared_log_payload
tree_consistency: pass
orphan_events: 0
destination_tag_missing: 1
id_generation_policy: caller_supplied"""

assert render_report(
    tracer,
    root_id,
    destination_tag_missing=count_missing_destination_tags(destination_log),
    id_generation_policy="caller_supplied",
) == expected_report
```

LangChain's tracing APIs demonstrate this at framework level: chat model, tool, and retriever callbacks receive `run_id`, optional `parent_run_id`, tags, and metadata. Event-stream tracing stores run and parent maps, emits events with run IDs and parent IDs, and assigns a UUID when no run ID is supplied.

ADK uses the invocation-scoped variant. `InvocationContext` owns an `invocation_id`, session events can be filtered to the current invocation, each `Event` has an `invocation_id`, and each event has its own unique `id`. Different shape, same purpose: make causality queryable.

## Determinism Move

Causal Tag constrains `ambient_state` by stamping every event with a queryable identity. The verifier filters the agent's contributions out of shared logs, traces, and message buses instead of accepting any matching event.

It constrains `async_timing` by replacing "this happened around the same time" with "this event carries the parent ID of the action." Parentage remains queryable across batching, reordering, delayed delivery, and concurrent producers.

## Observable Signal

Every Causal Tag report should include:

* run or invocation ID;
* parent run or event ID, null only for roots;
* propagation surfaces checked, such as trace store, log payload, message attribute, API header;
* tag presence per surface;
* tree consistency result;
* orphan-event count and destination-tag-miss count;
* ID generation policy (`caller_supplied`, `framework_assigned`, `uuid_on_missing`).

A useful report is a small join table:

```text
root_run_id: a001
event: agent.start run: a001 parent: null tag_present: trace_store
event: tool.start run: b002 parent: a001 tag_present: trace_store
event: handler.received run: b002 parent: a001 tag_present: trace_store, shared_log_payload
propagation_surfaces_checked: trace_store, shared_log_payload
destination_tag_observed: shared_log_payload
tree_consistency: pass
orphan_events: 0
destination_tag_missing: 1
id_generation_policy: caller_supplied
```

## Failure Modes

* **Time-Window Attribution:** Tests filter shared logs by path and timestamp. Any matching event after the start time can satisfy the assertion. Include a unique tag in the payload and require the observed event to carry it.
* **Framework Bypass:** The framework offers `run_id` and `parent_run_id`, but custom code emits events outside that path. Use the framework callback or explicitly propagate the IDs.
* **Flat ID Tree:** Every event has an ID, but no parent link. The verifier sees a bag of events, not a causal chain. Record parent IDs and assert tree consistency.
* **Tagged at Source, Untagged at Destination:** The outbound message has an ID, but the downstream log or callback drops it. Verify propagation across the boundary, not only at the source.

## Use When

Use this pattern when:

* the agent emits events into shared logs, traces, message buses, APIs, or side-effect targets;
* multiple agents, runs, or producers share the same event surface;
* async timing, batching, or reordering makes temporal proximity unreliable;
* verification must attribute an observed effect to a specific action;
* a framework tracing layer exists but is not yet engaged.

## Do Not Use When

Do not reach for Causal Tag when:

* the event surface is fully private to the test or run;
* **State Baseline** plus **Delta** gives equivalent attribution more cheaply;
* the boundary cannot carry any metadata and cannot be changed;
* the side effect is low stakes and misattribution cost is negligible.

When tags cannot propagate, redesign the boundary or fall back to snapshot-based attribution.

## Evidence

* **Verification Design Principle 9:** The design doc requires assertions to prove that the system's action caused the outcome. Causal Tag is the identity-based partner to State Baseline's snapshot-based answer.
* **[LangChain](https://github.com/langchain-ai/langchain) tracing:** The evidence summary records callback APIs that carry `run_id`, `parent_run_id`, tags, and metadata through chat model, tool, and retriever events.
* **LangChain event stream:** The same evidence records run maps, parent maps, emitted run IDs, parent IDs, and UUID assignment when run IDs are missing.
* **[ADK](https://github.com/google/adk-python) InvocationContext and Event:** The evidence summary records invocation IDs, per-event IDs, current-invocation event filtering, and function-response resolution by invocation.
* **ADK remote trigger tests:** The Delta sweep records the antipattern: Cloud Run logs are counted by path and timestamp without a unique message or test-run ID.

## Related Patterns

* **Delta:** requires tagged events to attribute changes. Delta on untagged shared logs is the Causal Tag antipattern.
* **State Baseline:** provides snapshot-based attribution when tag propagation is infeasible.
* **Trajectory Cursor:** cursor entries should carry causal tags so distributed events can be joined back to steps.
* **Guardrail Decorator:** guardrail interventions should emit tagged parent events.
* **Executable Analog:** tag-presence and tree-consistency checks are executable checks over the trace surface.
