# Effect Witness

*(Orchestration Pattern)*

## Name

**Effect Witness**

## Intent

Replay the same proposal from the same initial state under approval and rejection, then verify in the system of record that approval produces exactly one matching effect and rejection leaves none.

## Problem

A refund workflow can display "rejected" while its batch worker still posts the refund. Its interactive path can honor the verdict while a retry, resumed session, or parallel branch proceeds on stale state. A workflow can also record approval and then lose the approved operation before it posts. A test of the gate's return value passes in both cases because the ledger was outside the test.

The same question applies when cancellation or a failed check is supposed to stop a release. A model can receive a warning and continue. When a workflow promises to block, the observable contract is what happens at the release boundary after the verdict.

## Forces

The following are design judgments about the test contract.

* **Both decisions matter.** A rejection-only test can pass when the workflow drops all work. An approval-only test can pass when the workflow commits regardless of the decision. Report both rates together, with distinct denominators for rejected and eligible approved runs.
* **The record must answer the question.** A gate log can establish that a decision was recorded. A transcript can explain what the agent saw. Use the ledger to establish whether money was credited. Use the other records to diagnose a discrepancy after observing it.
* **Enforcement has a coverage cost.** A workflow that withholds a release after a failed check may convert wrong releases into abstentions. Record these as withheld outcomes and report correct, wrong, and withheld outcomes together where those categories apply.
* **Replay covers named paths.** A successful interactive run says little about a path that restores a queued job. Include resume, retry, parallel branches, and direct calls when they can commit the protected effect. Name any paths left untested.

## Solution

Choose an observable effect and write down its expected cardinality under each decision before running the workflow. Pin the proposal, initial records, path, and observation horizon for each pair. Change the decision between the two runs. Read the committed records independently of the gate under test and compare each count with its expectation.

Repeat the pair for every entry point in scope. Where multiple writers can act on the same proposal, add a combined-path case and expect one approved effect across all writers. Report how paths were selected and where the harness stopped observing. A delayed posting after that horizon falls outside the reported result.

## Mechanism

Select a witness tied to the proposal. In the refund example the entry matches the order, account, and amount in cents. In a ledger that permits repeated refunds of the same amount on one order, include a stable request identifier so a legitimate earlier refund cannot satisfy a new assertion.

Restore accounts and entries before every run. Supply the decision at the gate's input, then invoke the normal entry point and let the workflow run to the declared observation point. Read the ledger afresh. Evaluate both checks even when one fails, so the report distinguishes an unexpected release from missing completion.

In this example the workflow is synchronous, so return from the entry point is the observation point. An asynchronous workflow needs a completion signal or a bounded observation window for queued work. If the witness cannot be read or a worker is still pending at the boundary, record the observation as unknown with its reason.

## Pattern / Antipattern

### Antipattern: assert the refund verdict

The test supplies a rejection on the batch path and checks the verdict returned by the orchestrator. The return value can be correct even when the batch worker posts a refund.

```python
ledger = Ledger()
proposal = Refund(order=42, account="buyer", cents=2500)

verdict = batch_ignores_gate(ledger, proposal, "reject", "batch")

assert verdict == "rejected"
```

### Pattern: replay both decisions and read the refund ledger

The interactive route handles a live refund and the batch route handles queued refunds. Each row starts with identical accounts and entries. Three implementations exercise the witness: a batch route that ignores rejection, a corrected orchestrator, and an interactive route that drops approved work.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Refund:
    order: int
    account: str
    cents: int


@dataclass
class Ledger:
    accounts: dict[str, int] = field(default_factory=lambda: {"buyer": 10_000})
    entries: list[Refund] = field(default_factory=list)

    def post_refund(self, proposal: Refund) -> None:
        self.accounts[proposal.account] += proposal.cents
        self.entries.append(proposal)


def approval_gate(decision: str) -> str:
    return {"approve": "approved", "reject": "rejected"}[decision]


def batch_ignores_gate(ledger, proposal, decision, path):
    verdict = approval_gate(decision)
    if path == "batch" or verdict == "approved":
        ledger.post_refund(proposal)
    return verdict


def both_paths_check_gate(ledger, proposal, decision, path):
    verdict = approval_gate(decision)
    if verdict == "approved":
        ledger.post_refund(proposal)
    return verdict


def interactive_drops_approval(ledger, proposal, decision, path):
    if path == "interactive":
        return approval_gate(decision)
    return both_paths_check_gate(ledger, proposal, decision, path)


def check_refunds(orchestrate, proposal):
    failures = []
    print(f"Implementation: {orchestrate.__name__}")
    for path in ("interactive", "batch"):
        for decision, expected in (("reject", 0), ("approve", 1)):
            ledger = Ledger()
            orchestrate(ledger, proposal, decision, path)
            observed = ledger.entries.count(proposal)
            passed = observed == expected
            print(
                f"  path={path} decision={decision} expected={expected} "
                f"observed={observed} passed={passed}"
            )
            try:
                assert passed
            except AssertionError:
                failures.append((path, decision))
    return failures


proposal = Refund(order=42, account="buyer", cents=2500)
assert check_refunds(batch_ignores_gate, proposal) == [("batch", "reject")]
assert check_refunds(both_paths_check_gate, proposal) == []
assert check_refunds(interactive_drops_approval, proposal) == [
    ("interactive", "approve")
]
```

The outer assertions check that the demonstration produces the intended failures. A regression test for the production implementation would require an empty failure list. The corrected function uses the same decision predicate for both entry points, which converge on one ledger write in this example.

## Determinism Move

Constrain `ambient_state` by constructing a fresh ledger for every decision and path. An approved posting left over from an earlier run could satisfy a later approval even if that run dropped the operation. A fixed starting state and proposal make each observed entry attributable to the replay in this isolated example.

## Observable Signal

Each row includes the implementation, path, decision, expected count, observed count, and comparison result. In the batch rejection fault, the batch row reads expected zero and observed one. In the dropped approval fault, the interactive approval row reads expected one and observed zero. The corrected implementation matches both decisions on both paths.

For a suite with multiple proposals, report unexpected effects among rejections and missing or duplicate effects among approvals, with counts and denominators for both. Keep incomplete observations visible. State that the toy example checks each entry point individually. It leaves retries, resume, simultaneous paths, direct writes, and late commits untested.

## Failure Modes

The following are design judgments about witness scope.

* **Premature observation.** A zero count before a queued worker can run gives an apparent pass. Observe through a declared boundary that accounts for delayed writes.
* **Partial witness.** A matching entry can coexist with an unrelated credit. Where collateral effects matter, also check the balance changes and other affected records. A count of matching entries answers only the cardinality claim.
* **Lost attribution.** When the same proposal can run in a shared environment, a matching entry may belong to a different attempt. Isolate the fixture or give the request an identity that survives retries and is visible at commit.
* **Verdict substituted for enforcement.** A warning or rejection in the agent transcript supplies evidence about what the workflow communicated. Read the system of record to establish whether the protected effect occurred.

## Use When

Use this pattern when the workflow promises that a decision changes what it commits and the same decision pair can be exercised safely from equivalent initial state. It fits approval and denial, as well as cases where a failed check is meant to prevent release. The approval side applies when the proposal remains eligible and the workflow promises completion after approval.

## Do Not Use When

Use a simulator or a reversible fixture when replay could create real refunds or other irreversible effects. When the effect cannot be witnessed within a meaningful window, report that limitation and use a narrower claim. If a new precondition can legitimately require reconfirmation after approval, define that outcome separately from a lost eligible action before counting failures.

## Evidence

These preprints provide bounded examples for review. The paired refund test is a design choice.

* One study reports that model-free probes on pinned agent-framework releases found sibling effects committing despite an approval pause. Its mediation repair depends on routing all relevant effects through the enforcement boundary. [arXiv:2607.14166](https://arxiv.org/abs/2607.14166)
* One study reports both protected effects after rejection and missing approved effects in selected workflow and harness replays. Its paired replay holds the protected operation and initial state fixed. The results describe selected mechanisms and repeated cases. [arXiv:2611.19237](https://arxiv.org/abs/2611.19237)
* One study compares warnings and enforced release checks on synthetic count tasks with targeted faults. Enforced checks withheld many answers, which makes abstention relevant when interpreting the observed wrong-answer results. [arXiv:2611.20595](https://arxiv.org/abs/2611.20595)
* One study compares a gold write expectation with logged commit events on airline and retail tau2-bench tasks. The boundary check determines whether an expected write occurred. Write content, timing, and overall policy compliance require further evidence. [arXiv:2611.14581](https://arxiv.org/abs/2611.14581)
* One study reports that simulator replay in multi-turn function calling identifies collateral calls that final-state scoring can miss. The finding concerns benchmark-defined effects and depends on the reference trajectories and simulator. [arXiv:2611.02978](https://arxiv.org/abs/2611.02978)

### References

| Source | Study |
| --- | --- |
| [arXiv:2607.14166](https://arxiv.org/abs/2607.14166) | Stop Means Stop: Measuring and Repairing the Enforcement Gap in Agent-Framework Control Primitives |
| [arXiv:2611.19237](https://arxiv.org/abs/2611.19237) | Auditable Authorization for LLM Agents: Empirical Evidence Across Model, Harness, and Workflow Layers |
| [arXiv:2611.20595](https://arxiv.org/abs/2611.20595) | Invariant-Aware Harness Enforcement to Protect LLM Agents from Silent API Failures |
| [arXiv:2611.14581](https://arxiv.org/abs/2611.14581) | When Evaluators of AI Agents Disagree: An Empirical Study of Native Scoring, LLM Judges, and Commit-Boundary Checks on tau2-bench |
| [arXiv:2611.02978](https://arxiv.org/abs/2611.02978) | CAREFUL-Bench: Effect-Aware, Judge-Free Evaluation of Multi-Turn LLM Function Calling |

## Related Patterns

* **Guardrail Decorator:** places policy at a call boundary. Effect Witness checks the system of record across that route and other routes that can commit.
* **Delta:** checks the state change after an action. Effect Witness pairs the two decisions from the same starting state and checks each result.
* **Escalation Chain:** routes a decision to an owner. Effect Witness checks what commits after the owner decides.
* **Backpressure:** feeds a failed check upstream for correction. Effect Witness checks whether the release stopped after the check failed.
* **State Baseline:** captures the starting record. Effect Witness restores it for each replay to make the decisions comparable.
