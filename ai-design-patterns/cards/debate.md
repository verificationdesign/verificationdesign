# Debate

*(Orchestration Pattern)*

## Name

**Debate**

Also known as: Structured Disagreement, Multi-Agent Debate, Roundtable.

## Intent

Run bounded disagreement among multiple roles before a decision, with turn order, round count, phase, and consensus threshold held in orchestration state instead of model discretion.

## Problem

Debate is easy to imitate and hard to get as structure.

The theatrical version looks busy:

* one model is asked to play several debaters;
* every role receives the same prompt and the same transcript;
* a model decides who should speak next;
* "consensus" appears when the transcript sounds settled;
* the discussion either converges immediately or keeps going until the context budget runs out.

That is not a debate mechanism. It is a role-play transcript. The system cannot tell whether disagreement was real, whether every participant got a turn, whether the decision followed a threshold, or whether the model simply declared agreement.

`verification_design.md` Principle 8 names the useful move: simulate debate before concluding. For systems work, the simulation has to be orchestrated. The useful artifact is not "several messages happened." It is a bounded record of who spoke, in which phase, under which stopping rule, and how the decision was counted.

## Forces

* **Single critic vs. multi-round disagreement.** Adversary is cheaper and often enough. Debate pays for several roles and rounds when the decision benefits from multiple positions.
* **Independent positions vs. shared-transcript contamination.** A shared transcript lets debaters respond to one another, but it can also pull them toward premature agreement.
* **Round cap vs. convergence detection.** A fixed cap is auditable. Model-detected convergence is flexible but can hide the stopping rule.
* **Consensus threshold vs. unanimity vs. majority.** The decision rule should be named before the debate starts.
* **Deterministic speaker schedule vs. model-chosen speaker.** A schedule is less expressive than a moderator model, but it makes turn taking inspectable.

## Solution

Externalize the debate state.

The orchestrator registers debater identities, selects the next speaker by a deterministic schedule, records each position under a schema, and applies a named decision rule. Consensus is not whatever the final model says. It is a counted condition, such as a threshold over votes, or a bounded failure to reach consensus after `max_rounds`.

The model may generate arguments. Code owns:

* participant ids;
* phase;
* current speaker;
* round count;
* maximum rounds;
* consensus threshold;
* vote tally;
* final decision rule.

## Mechanism

1. **Register debaters.** Store participant ids and the order in which they speak.
2. **Initialize debate state.** Set phase, round count, maximum rounds, consensus threshold, and decision rule.
3. **Select speakers by schedule.** The orchestrator chooses the next speaker, not a model.
4. **Collect structured positions.** Each turn records speaker id, round, stance, rationale, and vote.
5. **Apply the stopping rule.** Stop when the threshold is met or when the round cap is exhausted, and emit the vote tally and decision.

## Pattern / Antipattern

The same task: decide whether to release a risky migration after structured disagreement. The antipattern side is intentionally uncovered in this pass. The pattern side shows a minimal bounded loop where speaker selection and consensus are code-level facts.

### Antipattern: uncovered theatrical-debate instance

No strict Debate antipattern was promoted from the OSS bench surveyed for this catalog.

The natural failure shape is theatrical debate: role labels without independent positions, no round cap, no speaker schedule, and a model-declared consensus. That overlaps with **Adversary** when the "critic" is only a label, and with **Cross-Family** when all debaters share the same family and priors.

This card keeps the Antipattern instance empty rather than fabricating a code example. When a strict instance is mined, re-author this section around the assertion `speaker_selected_by == "model" or consensus_threshold is None`.

### Pattern: bounded round-robin debate

The structured implementation stores turn order and stopping rules outside the model.

```python
from collections import Counter
from dataclasses import dataclass
from typing import Literal


Phase = Literal["proposal", "critique", "revision", "consensus"]
DecisionRule = Literal["threshold_vote", "max_rounds_exhausted"]
Vote = Literal["release", "revise", "escalate"]


@dataclass(frozen=True)
class Turn:
    round_index: int
    speaker_id: str
    phase: Phase
    stance: str
    vote: Vote


@dataclass(frozen=True)
class DebateResult:
    debater_ids: tuple[str, ...]
    max_rounds: int
    rounds_run: int
    consensus_threshold: int
    speaker_schedule: tuple[str, ...]
    phase_sequence: tuple[Phase, ...]
    vote_tally: dict[Vote, int]
    decision: Vote
    decision_rule: DecisionRule
    speaker_selected_by: Literal["schedule"]
    transcript: tuple[Turn, ...]


def run_debate(
    debater_ids: tuple[str, ...],
    max_rounds: int,
    consensus_threshold: int,
    collect_turn,
) -> DebateResult:
    transcript: list[Turn] = []
    phases: list[Phase] = []
    schedule: list[str] = []
    decision: Vote | None = None
    decision_rule: DecisionRule = "max_rounds_exhausted"

    for round_index in range(1, max_rounds + 1):
        for phase in ("proposal", "critique", "revision", "consensus"):
            phases.append(phase)
            for speaker_id in debater_ids:
                schedule.append(speaker_id)
                turn = collect_turn(
                    round_index=round_index,
                    speaker_id=speaker_id,
                    phase=phase,
                )
                transcript.append(turn)

            votes = Counter(turn.vote for turn in transcript)
            winner, count = votes.most_common(1)[0]
            if count >= consensus_threshold:
                decision = winner
                decision_rule = "threshold_vote"
                break
        if decision is not None:
            break

    if decision is None:
        votes = Counter(turn.vote for turn in transcript)
        decision = votes.most_common(1)[0][0]

    return DebateResult(
        debater_ids=debater_ids,
        max_rounds=max_rounds,
        rounds_run=transcript[-1].round_index,
        consensus_threshold=consensus_threshold,
        speaker_schedule=tuple(schedule),
        phase_sequence=tuple(phases),
        vote_tally=dict(votes),
        decision=decision,
        decision_rule=decision_rule,
        speaker_selected_by="schedule",
        transcript=tuple(transcript),
    )


def collect_turn(round_index: int, speaker_id: str, phase: Phase) -> Turn:
    vote_by_speaker = {
        "planner": "release",
        "critic": "revise",
        "operator": "revise",
    }
    return Turn(
        round_index=round_index,
        speaker_id=speaker_id,
        phase=phase,
        stance=f"{speaker_id} position during {phase}",
        vote=vote_by_speaker[speaker_id],
    )


result = run_debate(
    debater_ids=("planner", "critic", "operator"),
    max_rounds=2,
    consensus_threshold=2,
    collect_turn=collect_turn,
)

assert result.rounds_run <= result.max_rounds
assert result.consensus_threshold == 2
assert result.decision_rule in {"threshold_vote", "max_rounds_exhausted"}
assert result.speaker_selected_by == "schedule"
```

AutoGPT's `multi_agent_debate.py` in `classic/original_autogpt/` has this shape as a legacy v1 instance. It names proposal, critique, revision, consensus, and execution phases; stores proposal and critique artifacts; exposes debater count, round count, consensus threshold, and voting mode; and moves through bounded rounds before consensus.

AutoGen's `RoundRobinGroupChat` is the speaker-schedule instance. Its manager persists the message thread, current turn, and next-speaker index, then selects exactly one participant per turn by round-robin order. Debate is orchestration state, not a model choosing who should speak next.

## Determinism Move

Debate constrains `criteria_drift` by putting the decision rule in code. Consensus means a named threshold, vote tally, or exhausted round budget, not the model's changing sense that the group now agrees.

It constrains `self_review_bias` by replacing one perspective with multiple recorded positions before the final decision. This does not guarantee independence, but it creates a place to inspect who argued what and whether a single role dominated.

The determinism move is putting the stopping rule and turn order in code, so consensus is a counted condition, not a vibe.

## Observable Signal

Every Debate report should include:

* debater ids;
* rounds run;
* maximum rounds;
* phase sequence;
* consensus threshold;
* vote tally;
* decision;
* decision rule;
* speaker schedule.

A useful report shows the counted decision:

```text
debater_ids: [planner, critic, operator]
rounds_run: 1
max_rounds: 2
phase_sequence: [proposal]
consensus_threshold: 2
vote_tally: {release: 1, revise: 2}
decision: revise
decision_rule: threshold_vote
speaker_schedule: [planner, critic, operator]
```

## Failure Modes

* **Theatrical Debate:** role labels exist, but every debater shares the same prompt, same model family, and same priors. Use Cross-Family when the disagreement needs real diversity.
* **Unbounded Debate:** there is no round cap, and a model decides when the group has converged. Set `max_rounds` and record why the loop stopped.
* **Model-Chosen Speaker:** the next speaker is chosen by a model rather than a schedule. Record the speaker-selection rule or use a round-robin order.
* **Phantom Consensus:** consensus is declared without a threshold or vote count. Require a named decision rule and a tally.

## Use When

Use this pattern when:

* a high-stakes decision benefits from several perspectives;
* a single Adversary pass is too narrow;
* the system can afford multiple roles and bounded rounds;
* the decision needs an auditable vote, threshold, or turn record;
* unresolved disagreement should route to Escalation Chain or Backpressure.

## Do Not Use When

Do not reach for Debate when:

* a single critic is enough. Use Adversary;
* an Executable Analog or Comparator can decide the property directly;
* token, latency, or provider cost cannot support multiple turns;
* all debaters are the same model, same prompt, and same family, with no recorded diversity.

If the debate cannot create independent positions or a counted stopping rule, do not call it debate.

## Evidence

* **Verification Design Principle 8:** the design doc names Simulate Debate and frames debate as a way to force counterargument before conclusion.
* **[AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) multi-agent debate:** the orchestration sweep records a direct Debate instance with explicit phases, separate proposal and critique artifacts, configurable debater count, round count, consensus threshold, and voting mode.
* **AutoGPT legacy caveat:** the same implementation lives in `classic/original_autogpt/`, so it is treated as a legacy v1 implementation rather than a current framework recommendation.
* **[AutoGen](https://github.com/microsoft/autogen) RoundRobinGroupChat:** the orchestration sweep records a direct speaker-schedule instance: message thread, current turn, next-speaker index, one selected participant per turn, max turns, and termination conditions.
* **No promoted antipattern:** the orchestration sweep did not promote a strict Debate antipattern; this card cross-references Adversary and Cross-Family rather than inventing one.

## Related Patterns

* **Adversary:** Debate generalizes the single-critic primitive into multi-round, multi-role disagreement.
* **Cross-Family:** makes debater diversity stronger by separating model families.
* **Escalation Chain:** receives unresolved debate outcomes when no safe consensus is reached.
* **Backpressure:** routes debate findings back to revision.
* **Adversarial Frame:** defines the default-no posture each debater can apply to other positions.
