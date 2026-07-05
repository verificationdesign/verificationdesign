# Adversary

*(Orchestration Pattern)*

## Name

**Adversary**

Also known as: Critic, Red-Team Role, Negative Channel.

## Intent

Assign a structurally separate role whose only job is to find failures in another role's output, and require that role to emit a negative channel the orchestrator can inspect.

## Problem

A proposer produces work. The same proposer is then asked to "also list weaknesses," or a critic role is placed beside the proposer but given the same context and an optional feedback prompt.

That can look like verification:

* the transcript contains a message from a role named `critic`;
* the prompt says "be critical";
* the critic gives suggestions before approval;
* the workflow can continue when the critic says the work looks acceptable.

The boundary still collapses when the proposer grades its own work or when the negative channel is optional. A critic that can return an empty feedback string without recording "no defect found" has not performed an adversarial pass. It has only added a chance for the model to rationalize the draft.

`verification_design.md` Principle 1 rejects self-review as a verification signal. Principle 7 names the stronger form: cross-family verification beats self-verification. Adversary is the single-role orchestration primitive underneath those principles. It makes who critiques whom a runtime fact, not a tone instruction.

## Forces

* **Separate role vs. single-agent self-critique.** A second role costs tokens and routing complexity; self-critique is cheaper but preserves the same blind spot.
* **Shared context vs. blind critique.** Full context is easy to pass, but it can contaminate the critic. A Blind Oracle or Cross-Family verifier may be needed for stronger independence.
* **Mandatory negative channel vs. optional feedback.** Optional feedback collapses to "looks good." A mandatory negative channel must either list defects or record an explicit no-defect verdict.
* **Single critic vs. panel.** One adversary is the primitive. Multi-round disagreement belongs to Debate.
* **Same family vs. cross-family.** A same-family adversary can still share latent priors with the proposer. Cross-Family strengthens the role boundary.

## Solution

Make adversarial assignment explicit in code.

The orchestrator names a proposer, names a critic, rejects `critic_id == proposer_id`, and requires a structured critique artifact. The artifact must contain:

* proposer identity;
* critic identity;
* a reference to the artifact being critiqued;
* weaknesses, including risks or rejected assumptions;
* suggestions or next action;
* a score or verdict, where this card's sample score is 0-100 and higher means more severe concern;
* an explicit `no_defect_found` verdict if no weakness is found.

The role label is not enough. The load-bearing structure is identity separation plus a required negative channel.

## Mechanism

1. **Assign role identities.** Give each proposal an `author_id`, and give each critique a distinct `critic_id`.
2. **Reject self-critique.** The orchestrator refuses to route a proposal back to its author as the adversary.
3. **Run the critic under a findings schema.** The critic returns structured weaknesses, suggestions, score, and verdict.
4. **Require a negative channel.** A `defects_found` verdict must include at least one weakness, and a `no_defect_found` verdict must include zero weaknesses.
5. **Route findings onward.** Findings gate release, route to Backpressure, or escalate. Routing is outside this card; the adversary only creates the failure signal.

## Pattern / Antipattern

The same task: evaluate a proposal before it can advance. The antipattern side is intentionally uncovered in this pass. The pattern side shows the minimal identity and negative-channel assertions a verifier can inspect.

### Antipattern: uncovered confirmatory-critic instance

No strict Adversary antipattern was promoted from the OSS bench surveyed for this catalog.

The natural failure shape is a confirmatory critic: a role named `critic` or `adversary` that shares the proposer's context, asks for constructive feedback, and can approve without recording weaknesses or an explicit no-defect verdict. That shape is already covered by **Admissibility Gate**. A same-family critic that is treated as independent evidence is already covered by **Cross-Family**.

This card keeps the Antipattern instance empty rather than inventing a second copy of those failures. When a strict instance is mined, re-author this section around the assertion `critic_id == proposal.author_id or negative_channel_present is False`.

### Pattern: separate critic with mandatory findings

The structured implementation refuses self-critique, binds the returned artifact to the routed proposal and critic, and validates that the verdict agrees with the negative channel.

```python
from dataclasses import dataclass
from typing import Literal


Verdict = Literal["defects_found", "no_defect_found"]


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    author_id: str
    content: str


@dataclass(frozen=True)
class Critique:
    proposal_id: str
    proposer_id: str
    critic_id: str
    weaknesses: tuple[str, ...]
    suggestions: tuple[str, ...]
    score: int
    verdict: Verdict


def require_adversary(proposal: Proposal, critic_id: str) -> None:
    if critic_id == proposal.author_id:
        raise ValueError("critic must be distinct from proposer")


def require_bound_critique(
    proposal: Proposal, requested_critic_id: str, critique: Critique
) -> None:
    if critique.proposal_id != proposal.proposal_id:
        raise ValueError("critique proposal_id must match proposal")
    if critique.proposer_id != proposal.author_id:
        raise ValueError("critique proposer_id must match proposal author")
    if critique.critic_id == proposal.author_id:
        raise ValueError("returned critic must be distinct from proposer")
    if critique.critic_id != requested_critic_id:
        raise ValueError("critique critic_id must match routed critic")


def require_negative_channel(critique: Critique) -> None:
    if critique.verdict == "defects_found" and not critique.weaknesses:
        raise ValueError("defects_found requires at least one weakness")
    if critique.verdict == "no_defect_found" and critique.weaknesses:
        raise ValueError("no_defect_found requires zero weaknesses")


def run_adversary(proposal: Proposal, critic_id: str, critic_fn) -> Critique:
    require_adversary(proposal, critic_id)
    critique = critic_fn(proposal=proposal, critic_id=critic_id)
    require_bound_critique(proposal, critic_id, critique)
    require_negative_channel(critique)
    return critique


def build_adversary_report(proposal: Proposal, critique: Critique) -> dict[str, object]:
    return {
        "proposal_id": proposal.proposal_id,
        "proposer_id": critique.proposer_id,
        "critic_id": critique.critic_id,
        "critic_distinct_from_proposer": critique.critic_id != proposal.author_id,
        "negative_channel_present": bool(critique.weaknesses)
        or critique.verdict == "no_defect_found",
        "weakness_count": len(critique.weaknesses),
        "critique_score": critique.score,
        "verdict": critique.verdict,
    }


def render_adversary_report(report: dict[str, object]) -> str:
    lines = [
        f"proposal_id: {report['proposal_id']}",
        f"proposer_id: {report['proposer_id']}",
        f"critic_id: {report['critic_id']}",
        "critic_distinct_from_proposer: "
        f"{str(report['critic_distinct_from_proposer']).lower()}",
        "negative_channel_present: "
        f"{str(report['negative_channel_present']).lower()}",
        f"weakness_count: {report['weakness_count']}",
        f"critique_score: {report['critique_score']}",
        f"verdict: {report['verdict']}",
    ]
    return "\n".join(lines)


proposal = Proposal(
    proposal_id="p-017",
    author_id="planner",
    content="Ship the migration without a rollback check.",
)


def critic_fn(proposal: Proposal, critic_id: str) -> Critique:
    return Critique(
        proposal_id=proposal.proposal_id,
        proposer_id=proposal.author_id,
        critic_id=critic_id,
        weaknesses=("No rollback check is defined.",),
        suggestions=("Add a rollback verification gate before release.",),
        score=42,
        verdict="defects_found",
    )


critique = run_adversary(proposal, critic_id="critic", critic_fn=critic_fn)
report = build_adversary_report(proposal, critique)


def expect_value_error(expected_message: str, action) -> None:
    try:
        action()
    except ValueError as exc:
        assert str(exc) == expected_message
    else:
        raise AssertionError(f"expected ValueError: {expected_message}")


expect_value_error(
    "critic must be distinct from proposer",
    lambda: run_adversary(proposal, critic_id="planner", critic_fn=critic_fn),
)


def bad_critique(**overrides) -> Critique:
    values = {
        "proposal_id": "p-999",
        "proposer_id": "other-planner",
        "critic_id": "critic-shadow",
        "weaknesses": ("A different flaw is reported.",),
        "suggestions": ("Route the proposal through the matching reviewer.",),
        "score": 90,
        "verdict": "defects_found",
    }
    values.update(overrides)
    return Critique(**values)


binding_cases = (
    (
        "critique proposal_id must match proposal",
        bad_critique(
            proposer_id=proposal.author_id,
            critic_id="critic",
        ),
    ),
    (
        "critique proposer_id must match proposal author",
        bad_critique(
            proposal_id=proposal.proposal_id,
            critic_id="critic",
        ),
    ),
    (
        "critique critic_id must match routed critic",
        bad_critique(
            proposal_id=proposal.proposal_id,
            proposer_id=proposal.author_id,
        ),
    ),
    (
        "returned critic must be distinct from proposer",
        bad_critique(
            proposal_id=proposal.proposal_id,
            proposer_id=proposal.author_id,
            critic_id=proposal.author_id,
        ),
    ),
)

for expected_message, returned_critique in binding_cases:
    expect_value_error(
        expected_message,
        lambda returned_critique=returned_critique: run_adversary(
            proposal,
            critic_id="critic",
            critic_fn=lambda **_: returned_critique,
        ),
    )

expect_value_error(
    "no_defect_found requires zero weaknesses",
    lambda: run_adversary(
        proposal,
        critic_id="critic",
        critic_fn=lambda **_: Critique(
            proposal_id=proposal.proposal_id,
            proposer_id=proposal.author_id,
            critic_id="critic",
            weaknesses=("Rollback is still unchecked.",),
            suggestions=("Add the missing rollback gate.",),
            score=65,
            verdict="no_defect_found",
        ),
    ),
)

assert critique.critic_id != proposal.author_id
assert report["negative_channel_present"] is True
assert report["critic_distinct_from_proposer"] is True
assert render_adversary_report(report) == """proposal_id: p-017
proposer_id: planner
critic_id: critic
critic_distinct_from_proposer: true
negative_channel_present: true
weakness_count: 1
critique_score: 42
verdict: defects_found"""
```

AutoGPT's `multi_agent_debate.py` has this shape as a legacy v1 instance. Its critique artifact records `critic_id`, `target_agent_id`, weaknesses, suggestions, and score. Its critique phase skips self-critique by skipping `j == i`, so a proposal owner does not critique itself. A silent skip has different failure semantics from the sample above: it can leave a proposal uncritiqued unless the surrounding debate loop accounts for missing pairings.

That same AutoGPT instance also belongs on Debate. The critique artifact and self-critique exclusion are the Adversary mechanic; the bounded multi-round exchange and consensus behavior are the Debate mechanic.

AutoGen's writer and critic example in the migration guide is a partial instance. The critic is a named role in a `RoundRobinGroupChat`, and `TextMentionTermination("APPROVE")` makes explicit approval the release condition. That shape is also Backpressure because unresolved critic feedback keeps the loop running.

## Determinism Move

Adversary constrains `self_review_bias` by making the proposer unable to satisfy the adversarial step alone. The critic identity is external to the proposal, and the assertion rejects `critic_id == proposer_id`.

A same-family critic can still share the proposer's blind spots. Adversary by itself does not constrain `same_family_bias`; the recorded role boundary is where Cross-Family can attach its enforced family check.

The determinism move is making the negative channel mandatory and the critic's identity external.

## Observable Signal

Every Adversary report should include:

* proposal id;
* proposer id;
* critic id;
* critic distinct from proposer boolean;
* negative-channel present boolean;
* weakness count;
* critique score, on a 0-100 concern scale where higher means more severe;
* verdict.

A useful report makes the role boundary visible:

```text
proposal_id: p-017
proposer_id: planner
critic_id: critic
critic_distinct_from_proposer: true
negative_channel_present: true
weakness_count: 1
critique_score: 42
verdict: defects_found
```

Downstream orchestration, such as Backpressure or Escalation Chain, records routing decisions separately.

## Failure Modes

* **Confirmatory Critic:** the role is named critic, but the prompt asks for constructive feedback and approval. Use Admissibility Gate so the critic must search for failure before approval.
* **Self-Critique:** the critic and proposer are the same role or model call. Assert identity separation before routing the critique.
* **Optional Negative Channel:** the critic can return empty feedback with no recorded `no_defect_found` verdict. Reject empty critiques unless the no-defect verdict is explicit.
* **Toothless Adversary:** findings are produced but never gate, revise, or escalate. Connect the report to Backpressure or Escalation Chain.

## Use When

Use this pattern when:

* a single proposer's blind spots are costly;
* the workflow can afford a second role;
* the system needs an explicit failure-search step before release;
* the critique should create a routable artifact, not only prose;
* later Backpressure, Escalation Chain, or Debate steps need a negative signal.

## Do Not Use When

Do not reach for Adversary when:

* the task is trivial and a second role would add process noise;
* the critic would be the same model, same prompt context, and same family, with no recorded independence;
* an Executable Analog or Comparator can decide the property without an LLM critic;
* the desired structure is multi-round disagreement among several roles. Use Debate for that.

If only a same-family critic is available, label the result as a weak adversarial pass and maximize executable checks around it.

## Evidence

* **Verification Design Principles 1 and 7:** the design doc rejects self-review as a verification signal and frames independent verification as stronger than same-family review.
* **[AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) multi-agent debate:** the orchestration sweep records a direct Adversary instance: `AgentCritique` names critic and target identities, records weaknesses and suggestions, and skips self-critique in the critique phase.
* **AutoGPT legacy caveat:** the same evidence comes from AutoGPT's legacy v1 codebase, so it is treated as a historical implementation, not a current framework recommendation.
* **[AutoGen](https://github.com/microsoft/autogen) writer and critic migration guide:** the orchestration sweep records a partial instance where a critic role must emit `APPROVE` before the writer/critic loop terminates.
* **No promoted antipattern:** the orchestration sweep did not promote a strict Adversary antipattern; this card cross-references Admissibility Gate and Cross-Family instead of inventing one.

## Related Patterns

* **Admissibility Gate**: defines the default-no and admissibility logic an adversary applies to each finding.
* **Cross-Family:** strengthens the adversary by making the critic come from a different model family.
* **Debate:** generalizes Adversary into multi-round, multi-critic disagreement.
* **Escalation Chain:** receives unresolved adversary findings when the critic cannot safely approve.
* **Backpressure:** routes adversary findings back to the proposer for revision.
