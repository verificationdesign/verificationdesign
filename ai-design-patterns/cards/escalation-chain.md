# Escalation Chain

*(Orchestration Pattern)*

## Name

**Escalation Chain**

Also known as: Handoff, Tiered Routing, Manager Delegation.

## Intent

Route work to a higher-authority or different-capability handler through a typed, validated handoff, so the next owner is code-level state instead of a model's memory of who to call.

## Problem

Escalation is often written as a prompt convention:

* "If you cannot handle this, ask the manager."
* "Escalate low-confidence answers."
* "Call a senior reviewer when uncertain."
* "Route failures to another agent."

Those instructions name a desired behavior, not a routing mechanism. The model still decides whether escalation is needed, which target to call, and whether the target is different from itself. It may retry the same failing handler, route to an unknown role, or send the work to the same model family that produced the failure.

No typed handoff means no inspectable target. No validated target means no guarantee the next handler exists. No depth cap means escalation can loop.

`verification_design.md` Principle 2 names the core independence rule: generation and verification should be separated so the verifier does not copy the same errors. Escalation Chain extends that rule to routing by analogy. A failed or low-confidence handler should transfer control to a validated next handler, not ask the same model to remember an escalation instruction. Principle 7 adds the same-family caveat: escalation within the same family is weaker than escalation across a real family or capability boundary.

## Forces

* **Prompt convention vs. typed handoff.** A sentence can be ignored or misremembered. A handoff object can be validated.
* **Model-chosen target vs. orchestrator-enforced target.** Letting the model choose is flexible, but it makes the next owner unauditable unless the target is checked against known participants.
* **Same-family escalation vs. independent escalation.** Routing to a sibling role in the same family is cheap, but it may preserve the same blind spot.
* **Bounded depth vs. unbounded loops.** A chain needs a depth cap so failure does not bounce forever.
* **Manager process vs. ad hoc delegation.** A manager adds ceremony, but it centralizes authority and delegation tooling.

## Solution

Represent escalation as a typed message or configured manager process.

The orchestrator defines known handlers, allowed targets, maximum depth, and the authority that may route work. When a handler cannot safely proceed, it emits a handoff artifact naming:

* source handler;
* target handler;
* reason;
* payload or work item.

The orchestrator validates the source and target against registered participants, checks that the source is the current handler, rejects self-escalation, enforces the allowed-target policy, computes depth from the recorded path, enforces the depth cap, and records the path. Retries are a Backpressure loop, not a self-handoff through this escalation boundary.

Escalation authority belongs in code. The model may propose a handoff. The orchestrator decides whether the handoff is valid.

## Mechanism

1. **Define handlers and tiers.** Register handler ids, capabilities, families, and allowed handoff targets.
2. **Define a handoff schema.** The schema carries source, target, reason, and payload. The orchestrator derives depth from the recorded path.
3. **Validate the route.** Reject unknown sources, unknown targets, source impersonation, self-escalation, disallowed transitions, and over-depth paths.
4. **Route through the orchestrator.** The orchestrator sets the next handler from the validated handoff, not from free prose.
5. **Record the escalation path.** Store source, target, reason, computed depth, max depth, performed checks, process mode, and path.

## Pattern / Antipattern

The same task: route a failed verification to a stronger handler. The antipattern side is intentionally uncovered in this pass. The pattern side shows a typed handoff whose target is validated before control moves.

### Antipattern: uncovered prompt-convention escalation

No strict Escalation Chain antipattern was promoted from the OSS bench surveyed for this catalog.

The natural failure shape is prompt-convention escalation: a model is told to ask a manager when stuck, but the routing target is not typed, not validated, and can loop back to the same handler or same family. Same-family escalation is already covered by **Cross-Family**. Label-only routing roles overlap with **Adversary** when the role name implies independence that the code does not enforce.

This card keeps the Antipattern instance empty rather than inventing one. When a strict instance is mined, re-author this section around the assertion `handoff.target not in participants or handoff.target == handoff.source`.

### Pattern: typed handoff with validated target

The structured implementation makes the escalation target a validated fact before routing.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Handler:
    handler_id: str
    family: str
    tier: int


@dataclass(frozen=True)
class Handoff:
    source: str
    target: str
    reason: str
    payload: str


@dataclass(frozen=True)
class EscalationResult:
    source_handler: str
    target_handler: str
    escalation_reason: str
    escalation_depth: int
    max_depth: int
    checks_performed: tuple[str, ...]
    process_mode: str
    next_handler: Handler
    path: tuple[str, ...]

    def to_report(self) -> dict[str, object]:
        return {
            "source_handler": self.source_handler,
            "target_handler": self.target_handler,
            "escalation_reason": self.escalation_reason,
            "escalation_depth": self.escalation_depth,
            "max_depth": self.max_depth,
            "checks_performed": self.checks_performed,
            "process_mode": self.process_mode,
            "path": self.path,
        }


def route_handoff(
    handoff: Handoff,
    participants: dict[str, Handler],
    allowed_targets: dict[str, set[str]],
    max_depth: int,
    path: tuple[str, ...],
) -> EscalationResult:
    checks = (
        "unknown_target",
        "source_identity",
        "allowed_transition",
        "self_escalation",
        "depth_cap",
    )

    if handoff.source not in participants:
        raise ValueError(f"unknown escalation source: {handoff.source}")
    if handoff.target not in participants:
        raise ValueError(f"unknown escalation target: {handoff.target}")
    if not path or path[-1] != handoff.source:
        raise ValueError("handoff source is not the current handler")
    if handoff.target == handoff.source:
        raise ValueError("self-escalation is not an escalation")
    if handoff.target not in allowed_targets.get(handoff.source, set()):
        raise ValueError("target is not allowed for this source")

    depth = len(path)
    if depth > max_depth:
        raise ValueError("escalation depth exceeded")

    return EscalationResult(
        source_handler=handoff.source,
        target_handler=handoff.target,
        escalation_reason=handoff.reason,
        escalation_depth=depth,
        max_depth=max_depth,
        checks_performed=checks,
        process_mode="typed_handoff",
        next_handler=participants[handoff.target],
        path=path + (handoff.target,),
    )


participants = {
    "writer": Handler(handler_id="writer", family="gpt", tier=1),
    "reviewer": Handler(handler_id="reviewer", family="claude", tier=2),
    "human": Handler(handler_id="human", family="human", tier=3),
}

allowed_targets = {
    "writer": {"reviewer"},
    "reviewer": {"human"},
    "human": set(),
}

handoff = Handoff(
    source="writer",
    target="reviewer",
    reason="low confidence after adversary finding",
    payload="migration plan requires independent review",
)

result = route_handoff(
    handoff=handoff,
    participants=participants,
    allowed_targets=allowed_targets,
    max_depth=2,
    path=("writer",),
)

expected_report = {
    "source_handler": "writer",
    "target_handler": "reviewer",
    "escalation_reason": "low confidence after adversary finding",
    "escalation_depth": 1,
    "max_depth": 2,
    "checks_performed": (
        "unknown_target",
        "source_identity",
        "allowed_transition",
        "self_escalation",
        "depth_cap",
    ),
    "process_mode": "typed_handoff",
    "path": ("writer", "reviewer"),
}


def assert_rejected(bad_handoff: Handoff, bad_path: tuple[str, ...]) -> None:
    try:
        route_handoff(
            handoff=bad_handoff,
            participants=participants,
            allowed_targets=allowed_targets,
            max_depth=2,
            path=bad_path,
        )
    except ValueError:
        return
    raise AssertionError("invalid handoff was accepted")


assert_rejected(
    Handoff(
        source="writer",
        target="ghost",
        reason="unknown target",
        payload="work item",
    ),
    ("writer",),
)
assert_rejected(
    Handoff(
        source="writer",
        target="writer",
        reason="self-target",
        payload="work item",
    ),
    ("writer",),
)
assert_rejected(
    Handoff(
        source="reviewer",
        target="human",
        reason="wrong source",
        payload="work item",
    ),
    ("writer",),
)
assert_rejected(
    Handoff(
        source="reviewer",
        target="writer",
        reason="disallowed transition",
        payload="work item",
    ),
    ("writer", "reviewer"),
)
assert_rejected(
    Handoff(
        source="reviewer",
        target="human",
        reason="over depth",
        payload="work item",
    ),
    ("writer", "human", "reviewer"),
)

assert result.next_handler.handler_id == handoff.target
assert result.to_report() == expected_report
```

AutoGen's `Swarm` team has this typed-handoff shape. It selects the next speaker only from handoff messages, validates that handoff targets are participants, persists the current speaker, and otherwise keeps the current speaker when no handoff occurs.

CrewAI's hierarchical process is the manager-process sibling. Its hierarchical mode requires a manager LLM or manager agent, routes hierarchical execution through a manager, and equips the manager with delegation tools. That is escalation as configured process mode rather than prompt convention.

## Determinism Move

Escalation Chain constrains `tool_boundary_ambiguity` by making transfer of control happen at a typed boundary. The handoff target is validated against participants before the next handler runs, rather than being held in model memory.

Escalating to a same-family sibling can still be useful for load or specialization. Escalation Chain by itself does not constrain `same_family_bias`; that requires Cross-Family's enforced family boundary at the verifier seam.

The determinism move is making the routing target a validated fact in code, not a model's recollection of who to call.

## Observable Signal

Every Escalation Chain report should include:

* source handler;
* target handler;
* escalation reason;
* escalation depth;
* maximum depth;
* checks performed;
* process mode, such as `typed_handoff` or `manager_process`;
* manager-present boolean for manager-process reports;
* path so far.

A useful report names the handoff:

```text
source_handler: writer
target_handler: reviewer
escalation_reason: low confidence after adversary finding
escalation_depth: 1
max_depth: 2
checks_performed: [unknown_target, source_identity, allowed_transition, self_escalation, depth_cap]
process_mode: typed_handoff
path: [writer, reviewer]
```

## Failure Modes

* **Prompt-Convention Escalation:** the prompt says "ask the manager," but no typed target is emitted or validated. Add a handoff object and reject unknown targets.
* **Self-Escalation:** the target is the source handler. Reject self-handoffs at this boundary. Retries belong in Backpressure, not in Escalation Chain.
* **Same-Family Escalation:** work routes to a role that shares the same model family and blind spot. Use Cross-Family when independence matters.
* **Unbounded Escalation:** the chain has no depth cap and loops among handlers. Record depth and enforce `max_depth`.
* **Unvalidated Target:** the handoff names a handler that is not registered. Reject before routing.

## Use When

Use this pattern when:

* failures or low-confidence decisions should route to a more capable handler;
* the system has tiers, specialists, managers, or humans;
* the next handler must be auditable;
* unresolved Adversary or Debate findings need a stronger route;
* same-family retry would be insufficient evidence of independence.

## Do Not Use When

Do not reach for Escalation Chain when:

* a flat single-handler design is enough;
* an Executable Analog or Comparator can decide the property without routing;
* the proposed target is the same model, same prompt, and same family;
* there is no owner capable of handling the escalated work;
* the chain cannot enforce a maximum depth.

If escalation cannot name and validate a different next owner, label it as retry, not escalation.

## Evidence

* **Verification Design Principle 2:** the design doc names independence between generation and verification; Escalation Chain applies that independence rule to routing by analogy after failure or low confidence.
* **Verification Design Principle 7:** the same design doc frames cross-family verification as stronger than self-verification, which supplies the same-family caveat for escalation targets.
* **[AutoGen](https://github.com/microsoft/autogen) Swarm:** the orchestration sweep records a direct typed-handoff instance: next speaker is selected from handoff messages, targets are validated against participants, and current speaker is persisted.
* **[CrewAI](https://github.com/crewAIInc/crewAI) hierarchical process:** the orchestration sweep records a direct manager-process instance: hierarchical mode requires a manager, routes execution through that manager, and supplies delegation tools.
* **No promoted antipattern:** the orchestration sweep did not promote a strict Escalation Chain antipattern; this card cross-references Cross-Family and Adversary rather than inventing one.

## Related Patterns

* **Backpressure:** routes failure back upstream for revision; Escalation Chain routes failure up or out to a different handler.
* **Cross-Family:** makes escalation independent when the target comes from a different model family.
* **Debate:** unresolved debate can escalate when no safe consensus is reached.
* **Adversary:** adversary findings can trigger escalation.
* **Causal Tag:** tags escalation events so the routing path is auditable across logs.
