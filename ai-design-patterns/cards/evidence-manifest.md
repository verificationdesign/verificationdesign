# Evidence Manifest

*(Context Pattern)*

## Name

**Evidence Manifest**

## Intent

Match criterion-specific source evidence to the evidence packet at the checker entry point. Require that match before issuing a verdict.

## Problem

A support agent says it confirmed an order's status and then issued a refund. The criterion asks whether the status lookup came first. The run record holds the lookup call and its result, followed by the refund call, but the renderer copies only message text. The packet still reads like a complete account, so the judge returns a verdict based on the agent's description. Replaying the packet preserves the omission. The check measured a description of the work, while the criterion concerns the actions and their order.

The same problem arises when a checkpoint receives a compacted trace, a source-grounded judge receives an answer without its source document, or a check for whether a reference is still current receives a record with a missing replacement link. Use the criterion and an independently captured source to detect gaps the packet alone can hide.

## Forces

These tradeoffs reflect design judgment.

* **Context budget.** Summaries and compaction can make a run fit inside a checkpoint's input budget. Identify which fields each criterion needs before choosing what to compact.
* **Scope of restoration.** Restoring provenance changes the judge's input, including for judgments made correctly from a shorter view. Restore the fields required by the criterion and preserve intentional exclusions.
* **Verification cost.** A packet digest can check identity against a previously verified reference. Field comparison needs source access and a criterion-specific contract. A digest computed after degradation can faithfully identify the degraded packet.
* **Outcome accounting.** A negative verdict says the work failed a criterion. An unavailable verdict says the checker lacked the evidence to apply it. Preserve both outcomes so that reported verdict accuracy can be read alongside assessment coverage.

## Solution

Keep a manifest that maps criteria to the fields they require. Define presence and equality for each field, including the event scope and order when those carry meaning. Compare those fields in the source record and the received packet. Allow the judge to apply the criterion only after every required field passes. A manifest can also declare fields that must be absent, for example a draft deliberately withheld from an independent checker.

## Mechanism

1. **Define the contract.** Pin the manifest to the criterion and identify the authoritative run or document record. Use a stable event identity or a defined sequence when the criterion depends on relationships across events.
2. **Capture both records.** Extract the required fields independently from the source. Capture the rendered packet at the checker's entry point, after any staging or compaction, and extract the same fields there.
3. **Validate and compare.** Validate the packet shape before extracting fields. Compare field presence, values, and types. Require evidence in both records. Equality can be defined on parsed structured data when serialization details carry no meaning. Preserve ordering where the criterion depends on it.
4. **Gate the assessment.** Pass the same checked packet to the judge when every check succeeds. On any failed check return `not_assessable` with the field observations and skip the judge. Route an unavailable assessment separately from an adverse verdict.
5. **Test the entry point.** Use a faithful fixture, a malformed packet, and fixtures that remove or change required evidence. Verify both the report and whether the judge was called.

## Pattern / Antipattern

Both examples review whether an order status lookup preceded a refund. The source is a sequence of steps with a role, text, and structured tool calls. The packet is a text serialization delivered to the judge entry point.

### Antipattern: verify the rendered packet against itself

The renderer drops the calls. The digest check hashes the same rendered packet twice, and the stub judge accepts the agent's account.

```python
import hashlib
import json


def review(source):
    packet = json.dumps([
        {"role": step["role"], "text": step["text"]} for step in source
    ])
    recorded = hashlib.sha256(packet.encode()).hexdigest()
    assert hashlib.sha256(packet.encode()).hexdigest() == recorded
    return judge(packet)


def judge(packet):
    return "pass" if "confirmed the order status" in packet else "fail"
```

### Pattern: compare source fields at the judge entry point

For this fixture, every step is in scope, and each step must carry its call list in both records. The step sequence and each call's name, arguments, and result are compared together. The fixtures include an omitted call list, malformed JSON, a changed refund result type, and an intact packet. Each report comes from a recording entry point that receives the serialized packet and invokes the stub only after checking it.

```python
import json


MANIFEST = {"status_before_refund": ("tool_calls",)}
SOURCE = [
    {"role": "assistant", "text": "I confirmed the order status.",
     "tool_calls": [{"name": "lookup_order", "arguments": {"id": "A12"},
                     "result": {"status": "delivered"}}]},
    {"role": "assistant", "text": "I issued the refund.",
     "tool_calls": [{"name": "refund_order", "arguments": {"id": "A12"},
                     "result": {"refunded": True}}]},
]


def render(source, *, include_calls):
    fields = ("role", "text", "tool_calls") if include_calls else ("role", "text")
    return json.dumps([{field: step[field] for field in fields} for step in source])


def judge(packet):
    calls = [call for step in json.loads(packet) for call in step["tool_calls"]]
    return "pass" if [call["name"] for call in calls] == [
        "lookup_order", "refund_order"
    ] else "fail"


received_packets = []
judged_packets = []


def strict_equal(source_value, packet_value):
    if type(source_value) is not type(packet_value):
        return False
    if isinstance(source_value, dict):
        return source_value.keys() == packet_value.keys() and all(
            strict_equal(value, packet_value[key]) for key, value in source_value.items()
        )
    if isinstance(source_value, list):
        return len(source_value) == len(packet_value) and all(
            strict_equal(left, right) for left, right in zip(source_value, packet_value)
        )
    return source_value == packet_value


def reject_constant(value):
    raise ValueError(f"{value} is not a JSON value")


def judge_entry(criterion, source, packet):
    received_packets.append(packet)
    reason = None
    try:
        received = json.loads(packet, parse_constant=reject_constant)
    except (ValueError, TypeError, RecursionError):
        reason = "packet is not valid JSON"
    else:
        if not isinstance(received, list) or not all(
            isinstance(step, dict) for step in received
        ):
            reason = "packet must be a list of objects"
    if reason:
        received = []

    checks = []
    for index in range(max(len(source), len(received))):
        source_step = source[index] if index < len(source) else {}
        packet_step = received[index] if index < len(received) else {}
        for field in MANIFEST[criterion]:
            source_present = field in source_step
            packet_present = field in packet_step
            checks.append({
                "field": f"steps[{index}].{field}",
                "source_present": source_present,
                "packet_present": packet_present,
                "source_value": source_step.get(field),
                "packet_value": packet_step.get(field),
                "match": source_present and packet_present
                and strict_equal(source_step[field], packet_step[field]),
            })
    missing = [
        row["field"] for row in checks
        if not (row["source_present"] and row["packet_present"])
    ]
    report = {"criterion": criterion, "checks": checks, "missing": missing}
    if reason:
        return dict(report, outcome="not_assessable", reason=reason)
    if not checks or not all(row["match"] for row in checks):
        return dict(report, outcome="not_assessable")
    judged_packets.append(packet)
    return dict(report, outcome="assessable", verdict=judge(packet))


criterion = "status_before_refund"
lossy = render(SOURCE, include_calls=False)
faithful = render(SOURCE, include_calls=True)

# The renderer drops both required call lists.
lossy_report = judge_entry(criterion, SOURCE, lossy)
assert lossy_report["outcome"] == "not_assessable" and "verdict" not in lossy_report
assert lossy_report["missing"] == ["steps[0].tool_calls", "steps[1].tool_calls"]
assert len(judged_packets) == 0

# An incomplete JSON array never reaches the judge.
malformed = "["
malformed_report = judge_entry(criterion, SOURCE, malformed)
assert malformed_report["outcome"] == "not_assessable"
assert malformed_report["reason"] == "packet is not valid JSON"
assert malformed_report["missing"] == lossy_report["missing"]
assert "verdict" not in malformed_report and len(judged_packets) == 0

# The refunded field changes from a Boolean to an integer.
changed_steps = json.loads(faithful)
changed_steps[1]["tool_calls"][0]["result"]["refunded"] = 1
changed = json.dumps(changed_steps)
changed_report = judge_entry(criterion, SOURCE, changed)
assert changed_report["outcome"] == "not_assessable"
assert changed_report["missing"] == []
assert [row["match"] for row in changed_report["checks"]] == [True, False]
assert "verdict" not in changed_report and len(judged_packets) == 0

# The intact packet reaches the judge.
faithful_report = judge_entry(criterion, SOURCE, faithful)
assert faithful_report["outcome"] == "assessable" and faithful_report["verdict"] == "pass"
assert faithful_report["missing"] == [] and all(row["match"] for row in faithful_report["checks"])

assert received_packets == [lossy, malformed, changed, faithful]
assert judged_packets == [faithful]
print(json.dumps([lossy_report, malformed_report, changed_report, faithful_report], indent=2))
```

## Determinism Move

The nearest listed variance source is `tool_boundary_ambiguity`. The manifest defines which fields must cross the handoff. That source concerns the shape of what crosses a boundary. The manifest goes further: a packet can have the right shape and still carry the wrong values, so compare each required field with the source before the judge interprets the evidence.

## Observable Signal

Report the criterion and, for each required field path, its presence and value on both sides and whether the values match. Include the assessment outcome and give a verdict only when assessment completes. For sensitive values, use design judgment to limit exposure while retaining enough detail to diagnose a mismatch. In the lossy fixture, the source has both call lists and the packet omits them. The malformed fixture reports the refusal reason and marks packet fields unavailable. The changed fixture has both lists, with a type mismatch in the refund result. The faithful fixture matches values and types at both steps.

## Failure Modes

These failure modes reflect design judgment.

* **Self-referential integrity check.** Rehashing a stored packet checks its bytes against the recorded digest. Use an independent source comparison to establish coverage before relying on that digest.
* **Wrong copy.** A renderer's output can pass before later staging changes it. Put enforcement at the entry point and bind it to the packet passed onward.
* **Weak manifest.** Requiring a call name alone can miss changed arguments, results, or order. Derive the contract from what would change the criterion's application and seed those changes in fixtures.
* **Incomplete source.** A faithful packet can preserve a deficient record. Require independent source coverage where acquisition itself is in question. An omitted link that is absent on both sides cannot be reconstructed by comparing the two copies.

## Use When

Use this pattern when the checker consumes a derived view and the criterion depends on identifiable source evidence. It fits a trace renderer, a delegation boundary, and checkpoints that can request exact provenance on demand.

## Do Not Use When

A checker reading required values directly from the authoritative store has no separate rendered copy to compare. Use source validation there. When there is no independent record, keep the assurance claim scoped to the evidence whose provenance can be established.

## Evidence

* One input-assurance study reused 30 AgentProcessBench trajectories. The original judge packets matched their recorded hashes while omitting every structured call. Separate integration tests used a recording stub to observe packet receipt after a failed build and after a staged copy changed. [arXiv:2611.02676](https://arxiv.org/abs/2611.02676)
* In a frozen-trajectory study across four benchmarks, exact provenance recovered 85.5% of pooled abstraction-induced failures and degraded 5.2% of pooled native-correct judgments that had survived abstraction. The study pools related configurations and shares AgentProcessBench with the input-assurance study. [arXiv:2611.18471](https://arxiv.org/abs/2611.18471)
* In an LLM-AggreFact comparison, three tested judges scored higher on balanced accuracy with source documents available than when judging blind. [arXiv:2610.15938](https://arxiv.org/abs/2610.15938)
* On matched RFC replacement cases with missing links, all tested judges caught fewer replacements with an authoritative damaged record than with the texts alone. The result is scoped to the sampled RFC cases and tested presentations. [arXiv:2611.01311](https://arxiv.org/abs/2611.01311)
* In the tested web-agent trajectories summarized in the abstract of Gaming the Judge, changing the reasoning text while holding actions and observations fixed changed judgments. For an action criterion, the design judgment here is to require the underlying actions and observations in the manifest. [arXiv:2601.14691](https://arxiv.org/abs/2601.14691)

### References

| Source | Study |
| --- | --- |
| [arXiv:2611.02676](https://arxiv.org/abs/2611.02676) | Does the Judge See What the Evaluation Requires? Input Assurance for LLM Agent Evaluation |
| [arXiv:2611.18471](https://arxiv.org/abs/2611.18471) | Do Verifier Judgments Survive Abstraction? Measuring Verification Transport for LLM Agent Evaluation |
| [arXiv:2610.15938](https://arxiv.org/abs/2610.15938) | The Anatomy of a Blind Spot: What an LLM Judge Must Be Shown, and How Much |
| [arXiv:2611.01311](https://arxiv.org/abs/2611.01311) | What Do LLM Judges Actually Verify? Matched Controls and Record Gaps for Document Currency |
| [arXiv:2601.14691](https://arxiv.org/abs/2601.14691) | Gaming the Judge: Unfaithful Chain-of-Thought Can Undermine Agent Evaluation |

## Related Patterns

* **Admissibility Gate:** decides what kind of evidence counts. Evidence Manifest checks whether the required evidence arrived intact.
* **Blind Oracle:** deliberately withholds the draft from the checker. The manifest can record that exclusion alongside the evidence the checker must receive.
* **Trajectory Cursor:** records what happened up to a checkpoint. Evidence Manifest compares the copy available at the checkpoint with the recorded events.
* **Causal Tag:** attributes events to a run. Evidence Manifest uses the attributed record to check which event fields survived delivery.
* **Fault Seed:** tests whether a checker catches a known defect. A dropped field in a packet is a negative fixture for the manifest check itself.
