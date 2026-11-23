# Fault Seed

*(Verification Pattern)*

## Name

**Fault Seed**

## Intent

Qualify a verification gate by measuring its rejection of known-wrong work in each failure class. Require known-good work to pass, and do both checks before relying on the gate.

## Problem

A release check for a library migration can run on every candidate, return the same verdict on replay, and still accept the behavior the migration was supposed to change. In the example below, the release changes how a rounding function handles exactly halfway values. The check covers ordinary positive inputs on either side of halfway. A repair that preserves the old tie rule passes every assertion.

A green release check answers a question about the candidate under its current assertions. Qualification asks a different question about the check itself. If a plausible wrong candidate violates the changed contract, will this gate reject it? Running the same ordinary inputs again provides the same candidate verdict. A known-wrong repair makes the missing coverage visible.

## Forces

The following tradeoffs are design judgment.

* **Plausibility and cost.** A repair that returns a constant may be cheap to construct and easy to catch. A repair that agrees on ordinary inputs and disagrees only at the changed boundary requires more care to author. Choose seeds that represent decisions a maintainer would consider plausible when implementing the change.
* **Independent derivation and maintenance.** Derive seeds and their expected behavior from the documented change or specification. Reusing the release suite as the source of expected behavior carries its omissions into the qualification suite. Pin the specification version so a later change can trigger review of both the gate and seeds.
* **Qualification and evidence size.** A threshold gives the release process an explicit decision rule. The denominator tells the reader how much work that rule actually exercised. A perfect result on one seed is evidence about that seed and leaves variation within the class open.
* **Coverage and reach.** A gate can only decide on what its entry point can observe. A behavioral output check can distinguish two repairs that return different values on the same observed input. A requirement about source provenance needs evidence from somewhere else.

## Solution

Keep a fixed, replayable set of wrong artifacts and at least one known-good control. Give each seed a failure class, the obligation it violates, and an independently justified expected verdict. Set the required catch rate for each class before running qualification. Exercise the same entry point and verdict used for actual release so the observed decisions include the behavior of that gate.

For each class, divide the number of rejected seeds by the number of eligible seeds run. A class below threshold or without an eligible measurement is unqualified. Record seeds outside the gate's reach with the missing observation and keep them out of that denominator. When the known-good control fails, withhold qualification even if all the negative seeds were rejected.

## Mechanism

1. **Identify the obligation.** Record the changed behavior and the evidence the release gate can inspect. Write down which classes the release process intends the gate to cover.
2. **Construct and label seeds.** For each class, make plausible wrong work that violates the obligation. Record a witness input or other evidence of the violation. Include clean work that demonstrates the expected path through the same gate.
3. **Declare thresholds.** Set class thresholds and identify any required class that currently lacks eligible seeds. Keep thresholds fixed across the comparison of gate versions.
4. **Run the release gate.** Submit the seeds and control through the release interface. Preserve their individual verdicts. Treat an interrupted or incomplete qualification run as missing measurement.
5. **Scope the release decision.** Require passing clean controls and qualified coverage for every class assigned to the gate. Route obligations outside its reach to a check with the required observations.

The toy example treats gate verdicts as Boolean results from assertion predicates. In a real runner, the report needs to distinguish a candidate rejected on the contract from a harness failure that prevented the assertion from running. Design judgment favors reviewing both the fixture and the rejection reason when a surprising pass or rejection changes the qualification decision.

## Pattern / Antipattern

A toy library rounds nonnegative integer tenths to whole units. Its old release rounded ties up. Its new release rounds ties to the even whole unit. Ordinary values still round to the nearest whole unit. For example, 16 tenths rounds to 2 in both versions, but 25 tenths rounds to 2 under the new contract.

### Antipattern: release on ordinary inputs

The candidate below carries forward the old rule. All of the familiar release assertions pass, so the release process approves it.

```python
def repair(tenths):
    return (tenths + 5) // 10


assert repair(14) == 1
assert repair(16) == 2
assert repair(24) == 2
print("release approved")
```

### Pattern: qualify the release gate with seeded repairs

One seed retains the old tie-up rule. Another interprets the new rule as rounding all ties down. That interpretation handles 25 tenths correctly but misses 15 tenths, where the even answer is 2. The two witnesses exercise both parities of the lower integer. The declared threshold is 1.0 for each class in this small example.

```python
from pprint import pprint


def round_ties_even(tenths):
    whole, remainder = divmod(tenths, 10)
    if remainder == 5:
        return whole + whole % 2
    return (tenths + 5) // 10


def round_ties_up(tenths):
    return (tenths + 5) // 10


def round_ties_down(tenths):
    return (tenths + 4) // 10


typical_cases = ((14, 1), (16, 2), (24, 2))
change_cases = ((25, 2), (15, 2))
seeds = (
    ("legacy repair", "old tie rule", round_ties_up),
    ("always round ties down", "tie parity mishandled", round_ties_down),
)
thresholds = {"old tie rule": 1.0, "tie parity mishandled": 1.0}


def release_check(repair, cases):
    observations = [
        {"tenths": tenths, "expected": expected, "observed": repair(tenths)}
        for tenths, expected in cases
    ]
    passed = all(row["observed"] == row["expected"] for row in observations)
    return {"verdict": "pass" if passed else "reject", "cases": observations}


def qualify(gate_name, cases):
    control = release_check(round_ties_even, cases)
    records = [
        {"seed": name, "failure_class": failure_class, **release_check(repair, cases)}
        for name, failure_class, repair in seeds
    ]
    classes = {}
    for failure_class, threshold in thresholds.items():
        selected = [row for row in records if row["failure_class"] == failure_class]
        rejected = sum(row["verdict"] == "reject" for row in selected)
        rate = rejected / len(selected) if selected else None
        classes[failure_class] = {
            "rejected": rejected,
            "tested": len(selected),
            "catch_rate": rate,
            "threshold": threshold,
            "qualified": (
                control["verdict"] == "pass" and rate is not None and rate >= threshold
            ),
        }
    return {"gate": gate_name, "known_good": control, "seeds": records, "classes": classes}


ordinary = qualify("typical inputs", typical_cases)
expanded = qualify("typical inputs plus release-note edges", typical_cases + change_cases)
for report in (ordinary, expanded):
    pprint(report, sort_dicts=False)
    assert report["known_good"]["verdict"] == "pass"

assert [row["verdict"] for row in ordinary["seeds"]] == ["pass", "pass"]
assert [row["verdict"] for row in expanded["seeds"]] == ["reject", "reject"]
assert all(row["catch_rate"] == 0.0 and not row["qualified"]
           for row in ordinary["classes"].values())
assert all(row["catch_rate"] == 1.0 and row["qualified"]
           for row in expanded["classes"].values())
```

## Determinism Move

Fault Seed pins the seed identities, expected verdicts, denominator rules, and thresholds before qualification. The nearest variance source is `criteria_drift` because the qualification decision would otherwise be open to changing thresholds or counting rules after seeing the results. The rounding example starts with fixed release criteria. Its original defect is an omission in those criteria, which the closed list does not name directly. The pinned decision rule governs qualification even when the gate under test already produces repeatable verdicts.

## Observable Signal

Report the gate version, contract version and seed set in a maintained qualification run. For each seed, show its identifier, failure class, verdict, and available evidence for that verdict. Report the same observations for the clean controls. For every declared class, show rejected and tested counts, catch rate, threshold, and qualification status. Include any seeds outside the gate's reach and the observation each would require.

The typical-input gate reports 0 of 1 rejected in each class. The expanded gate reports 1 of 1 in each class. Both gates pass the clean repair. The per-input records show why the added coverage takes two values in this example. Each faulty repair agrees with the new rule on one of the two tie cases.

## Failure Modes

These are design judgments about interpreting the report.

* **Easy seeds.** A suite full of repairs that fail on ordinary inputs can show a high catch rate while leaving the documented change untested. Keep witnesses that preserve familiar behavior around the changed obligation.
* **Equivalent seeds.** A different implementation may have the required behavior throughout the contract domain. Review its witness and label before counting it as a negative fixture. Record unresolved cases as pending review.
* **Unobservable faults.** A seed outside the interface's reach needs a separate evidence path. Record that limitation explicitly. An observable obligation with an absent assertion is a coverage miss and belongs in the measured rate.
* **Pooled rates.** A large class of easy catches can hide a class that passes unchecked. Keep the counts and decisions per class and confine the conclusion to the exercised seeds.
* **Rejection without discrimination.** A gate that refuses all inputs can appear to catch every fault. A clean control checks that the intended release path stays open.

## Use When

Use Fault Seed when a release decision depends on a named obligation, the gate can be replayed, and plausible wrong candidates can be labelled independently. It fits a migration that keeps most consumer behavior and changes a specific boundary. In design terms, mutation testing is the software-testing ancestor of this move.

Repeat qualification when the gate, contract, or input representation changes. Keep some independently authored cases available for reassessment if the development team has tuned the gate on the original seeds.

## Do Not Use When

Use a source-to-observation check first when the gate has no access to the evidence needed for the obligation. Defer class qualification when reviewers lack a defensible way to distinguish correct from incorrect work. A discovery exercise can still identify candidate faults and sharpen the specification, with the class left unqualified until reviewers can justify fixture labels.

## Evidence

* In a study of repairs for documented CPython, Node.js, and SQLite changes, the task-mean false-accept share across hidden-wrong procedures in the complete first repair menu on affected test tasks was 0.410 with typical inputs and 0.065 with an author-written release-note edge input. The authors constructed the repair menu and the visible and withheld cases. [arXiv:2611.08269](https://arxiv.org/abs/2611.08269)
* On a benchmark of news and long-document summarization faithfulness, SummaCConv reached 74.4% balanced accuracy averaged across the benchmark datasets. This aggregate result describes the evaluated datasets. [arXiv:2111.09525](https://arxiv.org/abs/2111.09525)
* In a study of rendered agent evaluation packets, both validation checkers accepted an unmatched result in constructed negative fixtures. The study distinguishes content coverage from identity to a recorded copy. [arXiv:2611.02676](https://arxiv.org/abs/2611.02676)
* A vision-language reward study audited constructed failure categories separately from ordinary responses. Removing its deterministic verifier left ordinary-response accuracy similar while false positives increased for responses missing a final answer. [arXiv:2605.30244](https://arxiv.org/abs/2605.30244)
* In a synthetic database specification benchmark, a specification-length baseline reached balanced accuracy comparable to the reported judge results on held-out records. This comparison supplies a benchmark control for interpreting detection scores. [arXiv:2610.12778](https://arxiv.org/abs/2610.12778)

### References

| Source | Study |
| --- | --- |
| [arXiv:2611.08269](https://arxiv.org/abs/2611.08269) | Accepted but Wrong: Silent Failures of LLM Code Repairs after API Migrations |
| [arXiv:2111.09525](https://arxiv.org/abs/2111.09525) | SummaC faithfulness evaluation |
| [arXiv:2611.02676](https://arxiv.org/abs/2611.02676) | Does the Judge See What the Evaluation Requires? Input Assurance for LLM Agent Evaluation |
| [arXiv:2605.30244](https://arxiv.org/abs/2605.30244) | Vision-language reinforcement learning with rubric rewards |
| [arXiv:2610.12778](https://arxiv.org/abs/2610.12778) | Leakage-Resistant Evaluation of AI-Generated Database Specifications in Specification-Driven Migration |

## Related Patterns

* **Executable Analog:** turns the claim into an executable check. Fault Seed measures which known failures that check rejects.
* **Comparator:** compares actual and expected values for a candidate. Fault Seed runs the resulting comparison on independently labelled candidates and measures discrimination.
* **Judge Harness:** perturbs inputs to measure a judge's consistency. Fault Seed introduces known-wrong work to measure rejection by a gate of any kind.
* **Adversary:** gives a role the job of searching for defects in an output. Fault Seed replays a fixed set of recorded faults to qualify the gate.
* **Constitution:** pins rules in an inspectable artifact. Fault Seed exercises the checks that implement those rules.
