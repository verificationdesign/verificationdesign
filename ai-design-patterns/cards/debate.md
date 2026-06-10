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
5. **Apply the stopping rule.** Stop when the threshold is met by distinct debaters' current votes or when the round cap is exhausted, and emit the vote tally and decision. The threshold check runs after every phase, so a debate can stop before critique or revision when the proposal votes already meet the rule. If the cap is exhausted without consensus, route the unresolved outcome to escalation.

## Pattern / Antipattern

The same task: decide whether to release a risky migration after structured disagreement. The antipattern side is intentionally uncovered in this pass. The pattern side shows a minimal bounded loop where speaker selection and consensus are code-level facts.

### Antipattern: uncovered theatrical-debate instance

No strict Debate antipattern was promoted from the OSS bench surveyed for this catalog.

The natural failure shape is theatrical debate: role labels without independent positions, no round cap, no speaker schedule, and a model-declared consensus. That overlaps with **Adversary** when the "critic" is only a label, and with **Cross-Family** when all debaters share the same family and priors.

This card keeps the Antipattern instance empty rather than fabricating a code example. When a strict instance is mined, re-author this section around observable model-chosen speaking or a missing counted threshold.

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
    rationale: str
    vote: Vote


@dataclass(frozen=True)
class TurnContent:
    stance: str
    rationale: str
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

    def to_report(self) -> str:
        debaters = ", ".join(self.debater_ids)
        phases = ", ".join(self.phase_sequence)
        tally = ", ".join(
            f"{vote}: {count}" for vote, count in self.vote_tally.items()
        )
        schedule = ", ".join(self.speaker_schedule)
        return "\n".join(
            [
                f"debater_ids: [{debaters}]",
                f"rounds_run: {self.rounds_run}",
                f"max_rounds: {self.max_rounds}",
                f"phase_sequence: [{phases}]",
                f"consensus_threshold: {self.consensus_threshold}",
                f"vote_tally: {{{tally}}}",
                f"decision: {self.decision}",
                f"decision_rule: {self.decision_rule}",
                f"speaker_schedule: [{schedule}]",
            ]
        )


def latest_vote_tally(transcript: list[Turn]) -> Counter[Vote]:
    latest_vote_by_speaker = {
        turn.speaker_id: turn.vote
        for turn in transcript
    }
    return Counter(latest_vote_by_speaker.values())


def run_debate(
    debater_ids: tuple[str, ...],
    max_rounds: int,
    consensus_threshold: int,
    collect_turn,
) -> DebateResult:
    if not debater_ids:
        raise ValueError("debater_ids must not be empty")
    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")

    transcript: list[Turn] = []
    phases: list[Phase] = []
    schedule: list[str] = []
    decision: Vote | None = None
    decision_rule: DecisionRule = "max_rounds_exhausted"
    votes: Counter[Vote] = Counter()

    for round_index in range(1, max_rounds + 1):
        for phase in ("proposal", "critique", "revision", "consensus"):
            phases.append(phase)
            for speaker_id in debater_ids:
                schedule.append(speaker_id)
                content = collect_turn(
                    round_index=round_index,
                    speaker_id=speaker_id,
                    phase=phase,
                )
                turn = Turn(
                    round_index=round_index,
                    speaker_id=speaker_id,
                    phase=phase,
                    stance=content.stance,
                    rationale=content.rationale,
                    vote=content.vote,
                )
                transcript.append(turn)

            votes = latest_vote_tally(transcript)
            winner, count = votes.most_common(1)[0]
            if count >= consensus_threshold:
                decision = winner
                decision_rule = "threshold_vote"
                break
        if decision is not None:
            break

    if decision is None:
        votes = latest_vote_tally(transcript)
        decision = "escalate"

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


def collect_turn(round_index: int, speaker_id: str, phase: Phase) -> TurnContent:
    vote_by_speaker = {
        "planner": "release",
        "critic": "revise",
        "operator": "revise",
    }
    return TurnContent(
        stance=f"{speaker_id} position during {phase}",
        rationale=f"{speaker_id} rationale during {phase}",
        vote=vote_by_speaker[speaker_id],
    )


result = run_debate(
    debater_ids=("planner", "critic", "operator"),
    max_rounds=2,
    consensus_threshold=2,
    collect_turn=collect_turn,
)

assert result.decision == "revise"
assert result.vote_tally == {"release": 1, "revise": 2}
assert result.decision_rule == "threshold_vote"
assert result.rounds_run == 1
assert tuple(turn.speaker_id for turn in result.transcript) == result.speaker_schedule
assert result.to_report() == """debater_ids: [planner, critic, operator]
rounds_run: 1
max_rounds: 2
phase_sequence: [proposal]
consensus_threshold: 2
vote_tally: {release: 1, revise: 2}
decision: revise
decision_rule: threshold_vote
speaker_schedule: [planner, critic, operator]"""


def split_vote_turn(round_index: int, speaker_id: str, phase: Phase) -> TurnContent:
    vote_by_speaker = {
        "planner": "release",
        "critic": "revise",
        "operator": "escalate",
    }
    return TurnContent(
        stance=f"{speaker_id} split position during {phase}",
        rationale=f"{speaker_id} split rationale during {phase}",
        vote=vote_by_speaker[speaker_id],
    )


split_result = run_debate(
    debater_ids=("planner", "critic", "operator"),
    max_rounds=2,
    consensus_threshold=2,
    collect_turn=split_vote_turn,
)

assert split_result.decision_rule == "max_rounds_exhausted"
assert split_result.decision == "escalate"
assert split_result.rounds_run == split_result.max_rounds
assert split_result.vote_tally == {"release": 1, "revise": 1, "escalate": 1}
```

AutoGPT's legacy `multi_agent_debate.py` has this shape as a v1 instance. It names proposal, critique, revision, consensus, and execution phases; stores proposal and critique artifacts; exposes debater count, round count, consensus threshold, and voting mode; and moves through bounded rounds before consensus.

AutoGen's `RoundRobinGroupChat` is the speaker-schedule instance. Its manager persists the message thread, current turn, and next-speaker index, then selects exactly one participant per turn by round-robin order. Debate is orchestration state, not a model choosing who should speak next.

## Determinism Move

Debate constrains `criteria_drift` by putting the decision rule in code. Consensus means a named threshold over current votes by distinct debaters, a vote tally, or exhausted round budget, not the model's changing sense that the group now agrees.

Debate also creates an inspectable record of who argued what and whether one role dominated. By itself, it does not constrain `self_review_bias`; use Cross-Family and Adversary when the system must enforce producer-verifier separation.

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
* **AutoGPT legacy caveat:** the same implementation lives in AutoGPT's legacy classic tree, so it is treated as a legacy v1 implementation rather than a current framework recommendation.
* **[AutoGen](https://github.com/microsoft/autogen) RoundRobinGroupChat:** the orchestration sweep records a direct speaker-schedule instance: message thread, current turn, next-speaker index, one selected participant per turn, max turns, and termination conditions.
* **No promoted antipattern:** the orchestration sweep did not promote a strict Debate antipattern; this card cross-references Adversary and Cross-Family rather than inventing one.

## Related Patterns

* **Adversary:** Debate generalizes the single-critic primitive into multi-round, multi-role disagreement.
* **Cross-Family:** makes debater diversity stronger by separating model families.
* **Escalation Chain:** receives unresolved debate outcomes when no safe consensus is reached.
* **Backpressure:** routes debate findings back to revision.
* **Adversarial Frame:** defines the default-no posture each debater can apply to other positions.
